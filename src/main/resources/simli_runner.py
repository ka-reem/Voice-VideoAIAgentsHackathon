import av
import time

# Override the AudioResampler initialization to fix the layout issue
def fixed_audio_resampler(*args, **kwargs):
    try:
        if "layout" in kwargs:
            if isinstance(kwargs["layout"], int):
                if kwargs["layout"] == 1:
                    kwargs["layout"] = "mono"
                elif kwargs["layout"] == 2:
                    kwargs["layout"] = "stereo"
            elif not isinstance(kwargs["layout"], (str, av.AudioLayout)):
                raise ValueError(f"Unsupported layout type: {type(kwargs['layout'])}")
        return original_audio_resampler(*args, **kwargs)
    except Exception as e:
        print(f"Audio resampler error: {e}")
        raise

# Backup the original AudioResampler constructor and apply patch
original_audio_resampler = av.AudioResampler
av.AudioResampler = fixed_audio_resampler

import asyncio
import cv2
import numpy as np
import sounddevice as sd
from simli import SimliClient, SimliConfig

async def wait_for_connection(client, timeout=10):
    print("Waiting for WebRTC connection...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if await client.isConnected():
            print("WebRTC connection established!")
            return True
        await asyncio.sleep(0.5)
    return False

async def handle_video_stream(client):
    print("Initializing video stream...")
    window_name = 'Simli Video Stream'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    frame_count = 0
    
    try:
        print("Requesting video stream...")
        async for video_frame in client.getVideoStreamIterator(targetFormat="RGB"):
            try:
                # Convert frame data to numpy array
                frame_data = np.frombuffer(video_frame, dtype=np.uint8)
                if frame_data.size == 0:
                    print("Empty frame received, continuing...")
                    continue
                
                # Reshape based on expected dimensions
                frame = frame_data.reshape((480, 640, 3))  # Adjust dimensions if needed
                
                print(f"Displaying frame {frame_count}, shape: {frame.shape}")
                cv2.imshow(window_name, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                
                frame_count += 1
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
            except Exception as frame_error:
                print(f"Frame processing error: {frame_error}")
                continue
                
    except Exception as e:
        print(f"Video stream error: {e}")
        import traceback
        traceback.print_exc()

async def handle_audio_stream(client):
    try:
        # Initialize audio stream
        stream = sd.OutputStream(
            samplerate=16000,
            channels=1,
            dtype=np.int16
        )
        stream.start()

        async for audio_frame in client.getAudioStreamIterator():
            # Play audio frame
            stream.write(np.array(audio_frame))
    except Exception as e:
        print(f"Audio stream error: {e}")
    finally:
        stream.stop()
        stream.close()

async def main():
    print("Initializing SimliClient...")
    # Configure SimliClient
    config = SimliConfig(
        # apiKey=
        # faceId=
        maxSessionLength=3600,        # Maximum session length in seconds
        maxIdleTime=600,              # Maximum idle time in seconds
    )
    client = SimliClient(config)

    try:
        print("Establishing connection...")
        await client.Initialize()
        
        # Wait for WebRTC connection
        if not await wait_for_connection(client):
            print("Failed to establish WebRTC connection")
            return

        print("Starting streams...")
        await asyncio.gather(
            handle_video_stream(client),
            handle_audio_stream(client)
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("Cleaning up...")
        cv2.destroyAllWindows()
        await client.close()
        print("Done.")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())