#!/usr/bin/env python3

import configargparse as argparse
import distutils.util
import logging
import os
import traceback
import gi
gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst


def str2bool(v):
    return bool(distutils.util.strtobool(v))


def resolve_pravega_stream(stream_name, default_scope):
    if stream_name:
        if "/" in stream_name:
            return stream_name
        else:
            if not default_scope:
                raise Exception("Stream %s given without a scope but pravega-scope has not been provided" % stream_name)
            return "%s/%s" % (default_scope, stream_name)
    else:
        return None


def bus_call(bus, message, loop):
    """Callback for GStreamer bus messages"""
    t = message.type
    if t == Gst.MessageType.EOS:
        logging.info("End-of-stream")
        loop.quit()
    elif t == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        logging.warning("%s: %s" % (err, debug))
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        logging.error("%s: %s" % (err, debug))
        loop.quit()
    elif t == Gst.MessageType.ELEMENT:
        details = message.get_structure().to_string()
        logging.info("%s: %s" % (message.src.name, str(details),))
    elif t == Gst.MessageType.PROPERTY_NOTIFY:
        details = message.get_structure().to_string()
        logging.debug("%s: %s" % (message.src.name, str(details),))
    return True


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(
        description="Read video from a Pravega stream, detect objects, write video with on-screen display to Pravega streams",
        auto_env_var_prefix="")
    parser.add_argument("--allow-create-scope", type=str2bool, default=True)
    parser.add_argument("--detection-model",
        default=os.path.join(root_dir, "../video-processing/models/yolov5/FP16/yolov5s.xml"))
    parser.add_argument("--gst-debug",
        default="WARNING,pravegasrc:LOG,timestampcvt:LOG,pravegatc:LOG,pravegasink:DEBUG")
    parser.add_argument("--input-stream", required=True, metavar="SCOPE/STREAM")
    parser.add_argument("--keycloak-service-account-file")
    parser.add_argument("--log-level", type=int, default=logging.INFO, help="10=DEBUG,20=INFO")
    parser.add_argument("--pravega-controller-uri", default="tcp://127.0.0.1:9090")
    parser.add_argument("--pravega-scope")
    parser.add_argument("--start-mode", default="earliest")

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)
    logging.info("args=%s" % str(args))
    logging.debug("Debug logging enabled.")

    args.input_stream = resolve_pravega_stream(args.input_stream, args.pravega_scope)

    # Print configuration parameters.
    for arg in vars(args):
        logging.info("argument: %s: %s" % (arg, getattr(args, arg)))

    # Set GStreamer log level.
    os.environ["GST_DEBUG"] = args.gst_debug

    # Standard GStreamer initialization.
    Gst.init(None)
    logging.info(Gst.version_string())
    loop = GObject.MainLoop()

    pipeline_description = (
        "pravegasrc name=pravegasrc\n" +
        "   ! decodebin\n" +
        "   ! videoconvert\n" +
        "   ! autovideosink\n" +
        "")

    logging.info("Creating pipeline:\n" +  pipeline_description)
    pipeline = Gst.parse_launch(pipeline_description)

    # This will cause property changes to be logged as PROPERTY_NOTIFY messages.
    pipeline.add_property_deep_notify_watch(None, True)

    pravegasrc = pipeline.get_by_name("pravegasrc")
    if pravegasrc:
        pravegasrc.set_property("controller", args.pravega_controller_uri)
        pravegasrc.set_property("stream", args.input_stream)
        pravegasrc.set_property("allow-create-scope", args.allow_create_scope)
        if args.keycloak_service_account_file:
            pravegasrc.set_property("keycloak-file", args.keycloak_service_account_file)
        pravegasrc.set_property("start-mode", args.start_mode)

    #
    # Start pipelines.
    #

    # Feed GStreamer bus messages to event loop.
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    logging.info("Starting pipelines")
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except:
        logging.error(traceback.format_exc())
        # Cleanup GStreamer elements.
        pipeline.set_state(Gst.State.NULL)
        raise
    
    logging.info("Stopping pipeline")
    pipeline.set_state(Gst.State.NULL)
    logging.info("END")


if __name__ == "__main__":
    main()

