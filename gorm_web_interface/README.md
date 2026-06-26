# GORM Web Interface

A ROS 2 package providing a web-based interface for controlling and monitoring the GORM rover's motor systems.

## Features

- **Motor Control**: Start and stop rover motors through a web interface
- **Real-time Connection**: WebSocket-based connection to ROS 2 via rosbridge
- **Responsive Design**: Modern, mobile-friendly interface using TailwindCSS
- **Status Monitoring**: Real-time status updates and error handling

## Dependencies

- `rosbridge_server`: Provides WebSocket interface to ROS 2
- `std_srvs`: Standard service definitions used for motor control

## Usage

### Launch the Web Interface

Start both the web server and rosbridge server:

```bash
ros2 launch gorm_web_interface web_interface.launch.py
```

Or with custom ports:

```bash
ros2 launch gorm_web_interface web_interface.launch.py web_port:=8080 rosbridge_port:=9090
```

### Access the Interface

Open your web browser and navigate to:
- `http://localhost:8080` (or your custom port)
- If running on the robot, use the robot's IP address

### Expected Services

The web interface expects the following ROS 2 services to be available:
- `/start_motors` (std_srvs/srv/Trigger)
- `/shutdown_motors` (std_srvs/srv/Trigger)

## Development

### Running Components Separately

Start just the web server:
```bash
ros2 run gorm_web_interface web_server
```

Start just rosbridge:
```bash
ros2 run rosbridge_server rosbridge_websocket
```

### File Structure

```
gorm_web_interface/
├── package.xml              # ROS 2 package definition
├── setup.py                 # Python package setup
├── setup.cfg               # Setup configuration
├── resource/               # ROS 2 resource files
├── launch/                 # Launch files
│   └── web_interface.launch.py
├── gorm_web_interface/     # Python package
│   ├── __init__.py
│   └── web_server.py       # Web server node
└── web/                    # Web assets
    └── index.html          # Main web interface
```

## Integration

This package can be integrated into larger launch files by including the web interface launch file:

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

web_interface = IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        get_package_share_directory('gorm_web_interface'),
        '/launch/web_interface.launch.py'
    ])
)
```
