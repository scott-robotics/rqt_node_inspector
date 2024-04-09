from rqt_node_inspector.common import Node, Topic
from rosidl_runtime_py import message_to_yaml

from threading import Thread

from rqt_py_common.message_helpers import get_message_class
from rclpy.node import Node as RosNode
from rclpy import spin


def _topics_tuple_to_dict(topics_tuple):
    topics = {}
    for topic, topic_types in topics_tuple:
        t = Topic(topic, topic_types[0])
        topics[str(t)] = t
    return topics


class Introspector:
    _node: RosNode = None

    def __init__(self):
        self._echos = {}

    @property
    def node(self) -> RosNode:
        if self._node is None:
            print("Initializing introspector ROS node")
            self._node = RosNode("node_introspector")
            # Spin in a separate thread so we don't block
            self._spin_thread = Thread(target=spin, args=(self._node,), daemon=True)
            self._spin_thread.start()

        return self._node

    def register_echo(self, topic: Topic, callback: callable):
        if topic not in self._echos:
            self._echos[topic] = self.node.create_subscription(
                get_message_class(topic.type()), topic.name(), callback, 10
            )

    def unregister_echo(self, topic: Topic):
        if topic in self._echos:
            self.node.destroy_subscription(self._echos[topic])
            del self._echos[topic]

    def get_all_topics(self) -> dict[Topic]:
        return _topics_tuple_to_dict(self.node.get_topic_names_and_types())

    def get_all_nodes(self) -> tuple[Node]:
        return [Node(name, ns) for name, ns in self.node.get_node_names_and_namespaces()]

    def get_outbound_connections(self, node: Node) -> dict[Topic]:
        topics = _topics_tuple_to_dict(self.node.get_publisher_names_and_types_by_node(node._name, node._namespace))
        return topics

    def get_inbound_connections(self, node: Node) -> dict[Topic]:
        topics = _topics_tuple_to_dict(self.node.get_subscriber_names_and_types_by_node(node._name, node._namespace))
        return topics

    def get_publishers(self, topic: Topic) -> tuple[Node]:
        info = self.node.get_publishers_info_by_topic(topic._name)
        return [Node(n.node_name) for n in info]

    def get_subscribers(self, topic: Topic) -> tuple[Node]:
        info = self.node.get_subscriptions_info_by_topic(topic._name)
        return [Node(n.node_name) for n in info]
