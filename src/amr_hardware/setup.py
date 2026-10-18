from setuptools import find_packages, setup

package_name = 'amr_hardware'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        ('share/' + package_name, ['package.xml']),
        (
            'share/' + package_name + '/launch',
            ['launch/wheel_odom.launch.py'],
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='AMR Developer',
    maintainer_email='user@example.com',
    description='ROS 2 hardware interface for an autonomous mobile robot',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'nano_bridge = amr_hardware.nano_bridge:main',
            'wheel_odom = amr_hardware.wheel_odom:main',
        ],
    },
)