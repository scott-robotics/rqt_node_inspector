from rqt_node_inspector.common import Node, Topic, Service

from threading import Thread
import yaml

from rclpy import spin, spin_until_future_complete
from rclpy.node import Node as RosNode
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from rclpy.topic_or_service_is_hidden import topic_or_service_is_hidden
from rosidl_runtime_py import set_message_fields, message_to_yaml


# Configure QoS profile for publishing and subscribing
_default_qos_profile = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST,
    depth=1
)


def _topics_tuple_to_dict(topics_tuple, include_hidden=False):
    topics = {}
    for topic, topic_types in topics_tuple:
        if not include_hidden and topic_or_service_is_hidden(topic):
            continue
        t = Topic(topic, topic_types[0])
        topics[str(t)] = t
    return topics


def _services_tuple_to_dict(services_tuple, include_hidden=False):
    services = {}
    for topic, service_types in services_tuple:
        if not include_hidden and topic_or_service_is_hidden(topic):
            continue
        s = Service(topic, service_types[0])
        services[str(s)] = s
    return services


class Introspector:
    _node: RosNode = None

    def __init__(self):
        self._echos = {}
        self._services = {}

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
                topic._class, topic.name(), callback, _default_qos_profile
            )

    def unregister_echo(self, topic: Topic):
        if topic in self._echos:
            self.node.destroy_subscription(self._echos[topic])
            del self._echos[topic]

    def call_service(self, service: Service) -> str:
        if service not in self._services:
            self._services[service] = self.node.create_client(
                service._class,
                service.name())

        try:
            values_dictionary = yaml.safe_load(service.request_definition)
            request = service.Request()
            if self._services[service].wait_for_service(timeout_sec=1.0):
                set_message_fields(request, values_dictionary)
                future = self._services[service].call_async(request)

                spin_until_future_complete(self.node, future)
                response = future.result()
                return message_to_yaml(response, no_arr=True)
            else:
                return "Service call timed out..."
        except Exception as e:
            return str(e)

    def get_all_topics(self) -> dict[Topic]:
        return _topics_tuple_to_dict(self.node.get_topic_names_and_types())

    def get_all_nodes(self) -> tuple[Node]:
        return [Node(name, ns) for name, ns in self.node.get_node_names_and_namespaces()]

    def get_outbound_connections(self, node: Node) -> dict[Topic]:
        topics = _topics_tuple_to_dict(
            self.node.get_publisher_names_and_types_by_node(node._name, node._namespace))
        return topics

    def get_inbound_connections(self, node: Node) -> dict[Topic]:
        topics = _topics_tuple_to_dict(
            self.node.get_subscriber_names_and_types_by_node(node._name, node._namespace))
        return topics

    def get_services(self, node: Node) -> dict[Service]:
        services = _services_tuple_to_dict(
            self.node.get_service_names_and_types_by_node(node._name, node._namespace))
        return services

    def get_publishers(self, topic: Topic) -> tuple[Node]:
        info = self.node.get_publishers_info_by_topic(topic._name)
        return [Node(n.node_name, n.node_namespace) for n in info]

    def get_subscribers(self, topic: Topic) -> tuple[Node]:
        info = self.node.get_subscriptions_info_by_topic(topic._name)
        return [Node(n.node_name, n.node_namespace) for n in info]
