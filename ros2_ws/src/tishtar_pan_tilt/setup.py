from setuptools import find_packages, setup

package_name = 'tishtar_pan_tilt'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sepid',
    maintainer_email='sepideh.shamsizadeh@gmail.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'pan_tilt_controller = tishtar_pan_tilt.pan_tilt_node:main',
            'pan_tilt_keyboard = tishtar_pan_tilt.keyboard_node:main',
        ],
    },
    )
