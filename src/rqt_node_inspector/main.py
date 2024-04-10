#!/usr/bin/env python3

import sys

from rqt_gui.main import Main


def main():
    sys.exit(
        Main().main(
            sys.argv,
            standalone="rqt_node_inspector.ros_node_inspector.RosNodeInspector",
        )
    )


if __name__ == "__main__":
    main()
