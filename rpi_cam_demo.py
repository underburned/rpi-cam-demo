import cv2 as cv
import numpy as np
from PyQt6.QtCore import QCoreApplication, QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication
import sys
from threading import Thread
from typing import Optional

import gi
gi.require_version('Gst', '1.0')
gi.require_version("GstApp", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import GLib, GObject, Gst, GstApp, GstVideo


class FrameViewer(QObject):
    window_closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.frame: Optional[np.ndarray] = None
        self.received_frame_count = 0
        # Fixes no image display bug
        cv.namedWindow("RpiCam")

    def on_receive_frame(self, frame: np.ndarray):
        self.frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
        cv.imshow("RpiCam", self.frame)
        cv.waitKey(1)
        self.received_frame_count += 1

    def on_close_window(self):
        cv.destroyWindow("RpiCam")
        cv.waitKey(1)
        self.window_closed.emit()


class RPiCameraGrabber(QObject):
    send_frame = pyqtSignal(np.ndarray)
    close_window = pyqtSignal()
    all_work_is_done = pyqtSignal()

    def __init__(self):
        super().__init__()
        # GStreamer
        self.loop = None
        self.loop_thread = None
        self.pipeline: Optional[Gst.Pipeline] = None
        self.grouping_bin: Optional[Gst.Bin] = None
        self.bus: Optional[Gst.Bus] = None
        self.camerasrc: Optional[Gst.Element] = None
        self.camera_src_pad: Optional[Gst.Pad] = None
        self.camerasrc_src_pad_probe_id = 0
        self.camerasrc_caps: Optional[Gst.Caps] = None
        self.queue: Optional[Gst.Element] = None
        self.videoconvert: Optional[Gst.Element] = None
        self.videoconvert_caps: Optional[Gst.Caps] = None
        self.videocrop: Optional[Gst.Element] = None
        self.appsink: Optional[Gst.Element] = None
        self.appsink_pad: Optional[Gst.Pad] = None
        self.appsink_sample: Optional[Gst.Sample] = None
        self.buffer: Optional[Gst.Buffer] = None

        self.width = 1536
        self.height = 864
        self.pixel_format = "RGB"
        self.fps = 30

        self.fv = FrameViewer()
        self.fv_t = QThread()
        self.fv_t.start()
        self.fv.moveToThread(self.fv_t)
        self.send_frame.connect(self.fv.on_receive_frame, Qt.ConnectionType.QueuedConnection)
        self.close_window.connect(self.fv.on_close_window, Qt.ConnectionType.QueuedConnection)
        self.fv.window_closed.connect(self.on_window_closed, Qt.ConnectionType.QueuedConnection)

        self.retrieved_frame_count = 0
        self.frame_num = 100

    def gst_init(self):
        self.loop = GLib.MainLoop()
        Gst.init(None)

    def gst_deinit(self):
        self.fv_t.quit()
        self.fv_t.wait()
        self.loop.quit()
        if self.loop_thread is not None:
            self.loop_thread.join()
        Gst.deinit()
        print("All work is done. Bye!")
        self.all_work_is_done.emit()

    def initialize(self):
        self.gst_init()
        self.initialize_pipeline()

    def initialize_pipeline(self):

        self.pipeline = Gst.Pipeline.new("pipeline")
        self.grouping_bin = Gst.Bin.new("grouping_bin")
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
        self.bus_connect_message_id = self.bus.connect('message', self.on_bus_call)

        caps_stream_type = "video/x-raw"
        # libcamerasrc
        self.camerasrc = Gst.ElementFactory.make('libcamerasrc', "src_libcamerasrc")
        self.camerasrc.set_state(Gst.State.READY)
        self.camerasrc.set_property("af-mode", 2)

        self.camera_src_pad = self.camerasrc.get_static_pad("src")
        self.camerasrc_src_pad_probe_id = self.camera_src_pad.add_probe(Gst.PadProbeType.BUFFER,
                                                                        self.on_src_data_grabbed)

        # tcambin_caps
        self.camerasrc_caps = Gst.Caps.new_empty()
        self.camerasrc_caps = Gst.Caps.from_string(f"{caps_stream_type}, "
                                                   f"width={self.width}, "
                                                   f"height={self.height}, "
                                                   f"format={self.pixel_format}, "
                                                   f"framerate={self.fps}/1")
        # queue
        self.queue = Gst.ElementFactory.make('queue', "src_queue")

        # videoconvert
        self.videoconvert = Gst.ElementFactory.make('videoconvert', "src_videoconvert")

        # appsink
        self.appsink = Gst.ElementFactory.make("appsink", 'src_appsink')
        self.appsink.set_property("emit-signals", True)
        self.appsink.set_property("max-buffers", 1000)
        self.appsink.set_property("drop", False)
        self.appsink.set_property("wait-on-eos", True)
        self.appsink.set_property('sync', False)
        self.appsink.connect("new-sample", self.on_src_retrieve_frame)

        # Add elements to pipeline
        # Add to group bin
        self.grouping_bin.add(self.camerasrc)
        self.grouping_bin.add(self.queue)
        self.grouping_bin.add(self.videoconvert)
        # if self.src_frame_crop_enable:
        #     self.gst_add_element_to_grouping_bin(self.src_grouping_bin, self.src_videocrop)
        self.grouping_bin.add(self.appsink)
        self.pipeline.add(self.grouping_bin)

        # Link elements with each other
        self.camerasrc.link(self.queue)
        self.queue.link_filtered(self.videoconvert, self.camerasrc_caps)
        # if self.src_frame_crop_enable:
        #     self.gst_link_elements(self.src_videoconvert, self.src_videocrop)
        #     self.gst_link_elements(self.src_videocrop, self.src_appsink)
        # else:
        self.videoconvert.link(self.appsink)

    def start_grabbing(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        self.loop_thread = Thread(target=self.loop.run)
        self.loop_thread.start()

    def on_bus_call(self, bus: Gst.Bus, message: Gst.Message, *args):
        message_source: Optional[str] = message.src.get_name()
        message_type = message.type

        if message_type == Gst.MessageType.EOS:
            msg = f"EOS signal is received, stopping pipeline: {message_source}"
            print(f"SRC GSP: {msg}")
            self.close_window.emit()
        elif message_type == Gst.MessageType.STATE_CHANGED:
            old_state, new_state, pending_state = message.parse_state_changed()
            print(f"Pipeline state: {old_state} -> {new_state}")
        elif message_type == Gst.MessageType.ELEMENT:
            if message_source == self.grouping_bin.get_name() and message.has_name("GstBinForwarded"):
                forwarded_message: Gst.Message = message.get_structure().get_value("message")
                source_name = forwarded_message.src.get_name()

                if forwarded_message.type == Gst.MessageType.EOS:
                    if self.appsink.get_name() == source_name:
                        self.pipeline.set_state(Gst.State.NULL)
                    print(f"Source of EOS: {source_name}")
                    self.gst_deinit()
        elif message_type == Gst.MessageType.ERROR:
            error_msg, debug_msg = message.parse_error()
            print(f"SRC GSP: Error: {error_msg}: {debug_msg}")
            self.pipeline.set_state(Gst.State.NULL)
            self.loop.quit()
            self.loop_thread.join()
        return Gst.FlowReturn.OK

    def on_src_data_grabbed(self, pad: Gst.Pad, info: Gst.PadProbeInfo):
        pad_probe_return = Gst.PadProbeReturn.PASS
        return pad_probe_return

    def retrieve_frame(self):
        appsink_caps = self.appsink_sample.get_caps()
        appsink_frame_height = appsink_caps.get_structure(0).get_value('height')
        appsink_frame_width = appsink_caps.get_structure(0).get_value('width')
        appsink_frame_channels = int(self.buffer.get_size() /
                                     (appsink_frame_height * appsink_frame_width))
        appsink_frame_stream_format = appsink_caps.get_structure(0).get_value('format')
        appsink_frame_data = self.buffer.extract_dup(0, self.buffer.get_size())

        if appsink_frame_data:
            frame_image = np.frombuffer(appsink_frame_data, np.uint8).reshape(
                (appsink_frame_height, appsink_frame_width, appsink_frame_channels))
            print(f"retrieve_frame: {frame_image.shape}, frame count: {self.retrieved_frame_count}")
            self.send_frame.emit(frame_image)

    def on_src_retrieve_frame(self, appsink: Gst.Element):
        self.appsink_sample: Optional[Gst.Sample] = appsink.emit("pull-sample")
        if self.appsink_sample is not None:
            self.buffer: Gst.Buffer = self.appsink_sample.get_buffer()
            if self.buffer is not None:
                self.retrieved_frame_count += 1
                # print(f"Retrieved frame count: {self.retrieved_frame_count}")
                if self.retrieved_frame_count < self.frame_num:
                    self.retrieve_frame()
                else:
                    self.camerasrc.send_event(Gst.Event.new_eos())
            return Gst.FlowReturn.OK

    def on_window_closed(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.gst_deinit()


def main():
    app = QApplication(sys.argv)
    # QFontDatabase.addApplicationFont(":/usr/share/fonts/truetype/dejavu")

    rpcg = RPiCameraGrabber()
    rpcg.initialize()
    rpcg.all_work_is_done.connect(app.quit)
    rpcg.start_grabbing()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
