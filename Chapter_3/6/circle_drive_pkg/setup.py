from setuptools import setup

package_name = 'circle_drive_pkg'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/circle_drive.launch.py']),
        ('share/' + package_name + '/models', ['models/simple_robot.urdf']),
        ('share/' + package_name + '/worlds', ['worlds/world.sdf']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='student',
    maintainer_email='student@example.com',
    description='Gazebo World and Robot Circular Drive',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'circle_drive_node = circle_drive_pkg.circle_drive_node:main',
        ],
    },
)
