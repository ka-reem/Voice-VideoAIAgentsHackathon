import asyncio
from simli import SimliClient, SimliConfig
from aiohttp import web
import cv2
import numpy as np

# Configuration for SimliClient
config = SimliConfig(
    apiKey="zwdbatubh7hm5zgicg1j9",  # Replace with your API key
    faceId="6ebf0aa7-6fed-443d-a4c6-fd1e3080b215",        # Replace with your face ID
    maxSessionLength=3600,        # Maximum session length in seconds
    maxIdleTime=600,              # Maximum idle time in seconds
)

# Global variable to store the latest video frame
latest_frame = None

async def handle_video_frame(request):
    """HTTP handler to serve the latest video frame."""
    global latest_frame
    if latest_frame is None:
        print("No video frame available yet")  # Debug log for no frames
        return web.Response(status=204)  # No content

    # Encode the frame as JPEG and send it as a response
    success, jpeg_frame = cv2.imencode('.jpg', latest_frame)
    if not success:
        print("Failed to encode frame as JPEG")  # Debug log for encoding failure
        return web.Response(status=500)  # Internal server error

    print("Serving a video frame")  # Debug log for serving a frame
    return web.Response(body=jpeg_frame.tobytes(), content_type='image/jpeg')

async def process_video(simli_client):
    """Retrieve video frames from Simli SDK."""
    global latest_frame
    try:
        async for video_frame in simli_client.getVideoStreamIterator(targetFormat="RGB"):
            print("Received a video frame")  # Debug log for receiving frames

            # Convert video frame (Simli format) to OpenCV format (numpy array)
            try:
                frame = np.array(video_frame.to_ndarray())  # Convert PyAV VideoFrame to numpy array
                latest_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert RGB to BGR for OpenCV
            except Exception as e:
                print(f"Error processing video frame: {e}")  # Log any errors during processing

    except Exception as e:
        print(f"Error in process_video: {e}")  # Log any errors during video stream retrieval

async def main():
    """Main function to initialize SimliClient and start HTTP server."""
    async with SimliClient(config) as simli_client:
        print("SimliClient initialized.")

        # Start HTTP server for serving video frames
        app = web.Application()
        app.router.add_get('/video', handle_video_frame)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()
        print("HTTP server started at http://localhost:8080/video")

        # Process video frames concurrently with HTTP server
        await process_video(simli_client)

if __name__ == "__main__":
    print("Starting SimliClient...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopping Simli Connection")