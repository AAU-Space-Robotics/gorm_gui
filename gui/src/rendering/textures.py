# textures.py
import cv2
import OpenGL.GL as gl
import numpy as np


def load_texture_cv(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(f"Could not load texture: {path}")


    height, width = image.shape[:2]

    # Determine channel count
    if len(image.shape) == 2:
        # Grayscale -> convert to RGB
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        pixel_format = gl.GL_RGB
        internal_format = gl.GL_RGB
    elif image.shape[2] == 3:
        pixel_format = gl.GL_BGR
        internal_format = gl.GL_RGB
    elif image.shape[2] == 4:
        pixel_format = gl.GL_BGRA
        internal_format = gl.GL_RGBA
    else:
        raise ValueError(f"Unsupported image format with shape {image.shape}")

    texture_id = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)

    gl.glTexImage2D(
        gl.GL_TEXTURE_2D,
        0,
        internal_format,
        width,
        height,
        0,
        pixel_format,
        gl.GL_UNSIGNED_BYTE,
        image
    )

    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
    return texture_id, width, height


def create_empty_texture(width, height, channels=3):
    """
    Create an empty OpenGL texture that can be updated every frame.
    Returns: texture_id
    """
    texture_id = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)

    if channels == 3:
        internal_format = gl.GL_RGB
        pixel_format = gl.GL_RGB
    elif channels == 4:
        internal_format = gl.GL_RGBA
        pixel_format = gl.GL_RGBA
    else:
        raise ValueError("Only 3 (RGB) or 4 (RGBA) channels are supported")

    # Allocate GPU memory without initial data
    gl.glTexImage2D(
        gl.GL_TEXTURE_2D,
        0,
        internal_format,
        width,
        height,
        0,
        pixel_format,
        gl.GL_UNSIGNED_BYTE,
        None
    )

    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
    return texture_id


def update_texture_from_frame(texture_id, frame):
    """
    Update an existing OpenGL texture using an OpenCV frame.
    Returns: width, height, channels
    """
    if frame is None:
        raise ValueError("Frame is None")


    height, width = frame.shape[:2]

    # Convert frame to OpenGL-friendly format
    if len(frame.shape) == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        pixel_format = gl.GL_RGB
        internal_format = gl.GL_RGB
        channels = 3
    elif frame.shape[2] == 3:
        pixel_format = gl.GL_BGR
        internal_format = gl.GL_RGB
        channels = 3
    elif frame.shape[2] == 4:
        pixel_format = gl.GL_BGRA
        internal_format = gl.GL_RGBA
        channels = 4
    else:
        raise ValueError(f"Unsupported frame shape {frame.shape}")

    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)

    # Re-upload full frame
    gl.glTexImage2D(
        gl.GL_TEXTURE_2D,
        0,
        internal_format,
        width,
        height,
        0,
        pixel_format,
        gl.GL_UNSIGNED_BYTE,
        frame
    )

    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
    return width, height, channels


def delete_texture(texture_id):
    if texture_id:
        gl.glDeleteTextures([texture_id])