
import os

from ament_index_python import get_resource
from python_qt_binding import loadUi
from python_qt_binding.QtWidgets import QWidget
from python_qt_binding.QtCore import Signal

from rqt_node_inspector.ros2_introspection import Introspector, Node, Topic, message_to_yaml

from rqt_gui_py.plugin import Plugin


class QEchoWindow(QWidget):
    text_update_signal = Signal(str)

    def __init__(self, topic: str, on_close: callable = None):
        super().__init__()
        _, package_path = get_resource("packages", "rqt_node_inspector")
        ui_file = os.path.join(package_path, "share", "rqt_node_inspector", "resource", "RosTopicEcho.ui")
        loadUi(ui_file, self)

        self.seq = 0

        if on_close is not None:
            self._on_close = lambda: on_close(topic)
        else:
            self._on_close = None

        self.text_update_signal.connect(self._message_received)

        self.echoBrowser.setText("Waiting for messages...")

    def closeEvent(self, event):
        if self._on_close is not None:
            self._on_close()
        event.accept()
        self.deleteLater()

    def _message_received(self, text: str):
        self.echoBrowser.setText(text)
        self.label.setText(f"seq: {self.seq}")

    def update_echo(self, msg: any):
        self.seq += 1
        self.text_update_signal.emit(message_to_yaml(msg, no_arr=self.noArrFlag.isChecked()))


class RosNodeInspector(Plugin):

    def __init__(self, context):
        super(RosNodeInspector, self).__init__(context)
        self._node = context.node
        self._logger = self._node.get_logger().get_child("rqt_node_inspector.ros_node_inspector.RosNodeInspector")
        self.setObjectName("RosNodeInspector")

        self._widget = QWidget()
        self._echo_widget = {}

        _, package_path = get_resource("packages", "rqt_node_inspector")
        ui_file = os.path.join(
            package_path,
            "share",
            "rqt_node_inspector",
            "resource",
            "RosNodeInspector.ui",
        )
        loadUi(ui_file, self._widget)
        self._widget.setObjectName("RosNodeInspectorUi")
        self._widget.echoTabWidget.hide()
        if context.serial_number() > 1:
            self._widget.setWindowTitle(self._widget.windowTitle() + (" (%d)" % context.serial_number()))

        context.add_widget(self._widget)

        self._introspector = Introspector()
        self._refresh_node_list()
        self._topics = {}
        self._selected_topic: Topic = None

        self._widget.nodeRefreshButton.clicked.connect(self._refresh_node_list)
        self._widget.echoButton.clicked.connect(self._echo_topic)

        self._widget.nodeSelector.activated.connect(self._node_selected_callback)
        self._widget.leftTopicListWidget.itemClicked.connect(self._topic_selected_callback)
        self._widget.rightTopicListWidget.itemClicked.connect(self._topic_selected_callback)
        self._widget.leftNodeListWidget.itemClicked.connect(self._node_selected_from_list_callback)
        self._widget.rightNodeListWidget.itemClicked.connect(self._node_selected_from_list_callback)

    def _node_selected_from_list_callback(self, item):
        """ Callback the occurs when a Node is selected from the dropdown list """
        self._focus_node(self._nodes[item.text()])

    def _node_selected_callback(self, index):
        """ Callback the occurs when a Node is selected in one of the Lower panels """
        client = self._widget.nodeSelector.currentText()
        self._focus_node(self._nodes[client])

    def _topic_selected_callback(self, item):
        """ Callback the occurs when a Topic is selected in one of the Upper panels """
        self._focus_topic(self._topics[item.text()])

    def _focus_node(self, node: Node):
        """ When a Node is selected, display its inbound and outbound topics in the Upper panels """
        # Populate left with inbound connections
        entries = self._introspector.get_inbound_connections(node)
        self._topics.update(entries)

        self._widget.leftTopicListWidget.clear()
        self._widget.leftTopicListWidget.addItems(sorted(map(str, entries)))

        # Populate right with outbound connections
        entries = self._introspector.get_outbound_connections(node)
        self._topics.update(entries)
        self._widget.rightTopicListWidget.clear()
        self._widget.rightTopicListWidget.addItems(sorted(map(str, entries)))

        self._selected_topic = None

    def _focus_topic(self, topic: Topic):
        """ When a Topic is selected, display its Publishers and Subscribers
            topics in the Lower panels.
        """
        # Populate left with publishers
        entries = self._introspector.get_publishers(topic)
        self._widget.leftNodeListWidget.clear()
        self._widget.leftNodeListWidget.addItems(sorted([str(e) for e in entries]))

        # Populate right with subscribers
        entries = self._introspector.get_subscribers(topic)
        self._widget.rightNodeListWidget.clear()
        self._widget.rightNodeListWidget.addItems(sorted([str(e) for e in entries]))

        print(f"Selected topic: {topic}")
        self._selected_topic = topic

    def _echo_topic(self):
        """ Creates a new Tab in a separate panel to echo the Topic  """
        topic = self._selected_topic
        print(f"Echoing topic: {topic}")
        if topic not in self._echo_widget and topic is not None:
            self._echo_widget[topic] = QEchoWindow(topic, on_close=self._unecho_topic)
            index = self._widget.echoTabWidget.addTab(self._echo_widget[topic], topic.name())
            self._widget.echoTabWidget.setCurrentIndex(index)
            self._introspector.register_echo(topic, self._echo_widget[topic].update_echo)

        self._widget.echoTabWidget.show()

    def _unecho_topic(self, topic: Topic):
        """ Closes the Tab """
        print(f"Closing topic: {topic}")
        self._introspector.unregister_echo(topic)
        if topic in self._echo_widget:
            del self._echo_widget[topic]

        if not len(self._echo_widget):
            self._widget.echoTabWidget.hide()

    def _refresh_node_list(self):
        nodes = self._introspector.get_all_nodes()
        self._nodes = {str(n): n for n in nodes}

        self._widget.nodeSelector.clear()
        self._widget.nodeSelector.addItems(sorted(self._nodes.keys()))
