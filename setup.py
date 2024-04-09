from setuptools import setup

package_name = "rqt_node_inspector"
setup(
    name=package_name,
    version="1.0.0",
    package_dir={"": "src"},
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name + "/resource", ["resource/RosNodeInspector.ui", "resource/RosTopicEcho.ui"]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name, ["plugin.xml"]),
        ("lib/" + package_name, ["scripts/rqt_node_inspector"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    author="Terry Scott",
    maintainer="Terry Scott",
    maintainer_email="terry.s.02@gmail.com",
    keywords=["ROS"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development",
    ],
    description=("rqt_node_inspector provides a GUI plugin for visualizing the ROS computation graph."),
    license="BSD",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "rqt_node_inspector = rqt_node_inspector.main:main",
        ],
    },
)
