from setuptools import find_packages, setup

package_name = 'rover_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gareth-joel',
    maintainer_email='garethjoel77@gmail.com',
    description='CosmoKazi rover control: teleop, autonomy, and behavior tree nodes.',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'cmd_vel_mux_node = rover_control.cmd_vel_mux_node:main',
            'autonomy_navigator_node = rover_control.autonomy_navigator_node:main',
            'behavior_tree_node = rover_control.behavior_tree_node:main',
        ],
    },
)
