from setuptools import find_packages, setup
import os
from glob import glob


package_name = 'gorm_gui'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/gui.launch.py']),
        ('share/' + package_name + '/config', ['config/gorm_foxglove.json']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Jonas Thorhauge',
    maintainer_email='jonas.thorhauge@gmail.com',
    description='ROS 2 package for the launching and configuring the foxglove gui for GORM.',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gui_republisher = gorm_gui.gui_republisher:main',
        ],
    },
)
