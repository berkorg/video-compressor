import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null);
  const [compressedImageUrl, setCompressedImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [quality, setQuality] = useState<number>(15); // Default quality value
  const [fileSize, setFileSize] = useState<string | null>(null);
  const [originalFrameSize, setOriginalFrameSize] = useState<string | null>(null);
  const [compressedImageSize, setCompressedImageSize] = useState<string | null>(null);
  const [compressedVideoUrl, setCompressedVideoUrl] = useState<string | null>(null);
  const [compressedVideoSize, setCompressedVideoSize] = useState<string | null>(null);
  const [sizeReductionPercentage, setSizeReductionPercentage] = useState<number | null>(null);
  const [estimatedVideoSize, setEstimatedVideoSize] = useState<string | null>(null);
  const [isFrameCompressing, setIsFrameCompressing] = useState<boolean>(false);
  const [isVideoCompressing, setIsVideoCompressing] = useState<boolean>(false);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const videoFile = event.target.files[0];
      setFile(videoFile);
      setFileSize(formatFileSize(videoFile.size));
      try {
        const thumbnailBlob = await extractFirstFrame(videoFile);
        setThumbnailUrl(URL.createObjectURL(thumbnailBlob));
      } catch (err) {
        setError('Error extracting thumbnail');
        console.error(err);
      }
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleQualityChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(event.target.value, 10);
    setQuality(Math.min(Math.max(value, 1), 31)); // Ensure value is between 1 and 31
  };

  const extractFirstFrame = (videoFile: File): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const video = document.createElement('video');
      video.preload = 'metadata';
      video.onloadedmetadata = () => {
        video.currentTime = 0;
      };
      video.onseeked = () => {
        if (canvasRef.current) {
          const canvas = canvasRef.current;
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height);
          canvas.toBlob((blob) => {
            if (blob) resolve(blob);
            else reject(new Error('Failed to create blob'));
          }, 'image/jpeg');
        } else {
          reject(new Error('Canvas not available'));
        }
      };
      video.onerror = () => {
        reject(new Error('Error loading video'));
      };
      video.src = URL.createObjectURL(videoFile);
    });
  };

  const calculateSizeReduction = (originalSize: number, compressedSize: number) => {
    const reduction = ((originalSize - compressedSize) / originalSize) * 100;
    return Math.round(reduction * 100) / 100; // Round to 2 decimal places
  };

  const estimateCompressedVideoSize = (originalSize: number, reductionPercentage: number) => {
    const estimatedSize = originalSize * (1 - reductionPercentage / 100);
    return formatFileSize(estimatedSize);
  };

  const handleUpload = async () => {
    if (!file || !thumbnailUrl) {
      setError('Please select a video file');
      return;
    }

    setIsFrameCompressing(true);
    setError(null);

    try {
      // Create FormData and append the frame
      const formData = new FormData();
      const response = await fetch(thumbnailUrl);
      const blob = await response.blob();
      formData.append('file', blob, 'first_frame.jpg');
      formData.append('quality', quality.toString());

      setOriginalFrameSize(formatFileSize(blob.size));

      // Make the request to the server
      const serverResponse = await fetch('http://127.0.0.1:5000/compress', {
        method: 'POST',
        body: formData,
      });

      if (!serverResponse.ok) {
        throw new Error('Server error');
      }

      const data = await serverResponse.json();
      setCompressedImageUrl(data.s3_url);

      // Fetch the compressed image to get its size
      const compressedImageResponse = await fetch(data.s3_url);
      const compressedImageBlob = await compressedImageResponse.blob();
      setCompressedImageSize(formatFileSize(compressedImageBlob.size));

      // Calculate size reduction percentage
      const originalFrameBlob = await (await fetch(thumbnailUrl)).blob();
      const compressedFrameBlob = await (await fetch(data.s3_url)).blob();
      const reductionPercentage = calculateSizeReduction(originalFrameBlob.size, compressedFrameBlob.size);
      setSizeReductionPercentage(reductionPercentage);

      // Estimate compressed video size
      if (file) {
        const estimatedSize = estimateCompressedVideoSize(file.size, reductionPercentage);
        setEstimatedVideoSize(estimatedSize);
      }
    } catch (err) {
      setError(`Error uploading and compressing image: ${err}`);
      console.error(err);
    } finally {
      setIsFrameCompressing(false);
    }
  };

  const handleVideoUpload = async () => {
    if (!file) {
      setError('Please select a video file');
      return;
    }

    setIsVideoCompressing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('quality', quality.toString());

      const serverResponse = await fetch('http://127.0.0.1:5000/compress_video', {
        method: 'POST',
        body: formData,
      });

      if (!serverResponse.ok) {
        throw new Error('Server error');
      }

      const data = await serverResponse.json();
      setCompressedVideoUrl(data.s3_url);

      // Fetch the compressed video to get its size
      const compressedVideoResponse = await fetch(data.s3_url);
      const compressedVideoBlob = await compressedVideoResponse.blob();
      setCompressedVideoSize(formatFileSize(compressedVideoBlob.size));
    } catch (err) {
      setError(`Error uploading and compressing video: ${err}`);
      console.error(err);
    } finally {
      setIsVideoCompressing(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Video Frame Extractor and Compressor</h1>
        <input type="file" accept="video/*" onChange={handleFileChange} />
        {fileSize && <p>Current video file size: {fileSize}</p>}
        <div>
          <label htmlFor="quality">Compression Quality (1-31):</label>
          <input
            type="number"
            id="quality"
            min="1"
            max="31"
            value={quality}
            onChange={handleQualityChange}
          />
        </div>
        <div>
          <button onClick={handleUpload} disabled={!file || isFrameCompressing}>
            {isFrameCompressing ? 'Compressing Frame...' : 'Extract and Compress Frame'}
          </button>
          <button onClick={handleVideoUpload} disabled={!file || isVideoCompressing}>
            {isVideoCompressing ? 'Compressing Video...' : 'Compress Entire Video'}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
        {thumbnailUrl && (
          <div className="thumbnail-container">
            <h2>Extracted Thumbnail:</h2>
            <img src={thumbnailUrl} alt="Extracted thumbnail" className="thumbnail" />
          </div>
        )}
        {thumbnailUrl && compressedImageUrl && (
          <div className="comparison">
            <div className="original">
              <h2>Original First Frame:</h2>
              <img src={thumbnailUrl} alt="Original first frame" className="thumbnail" />
              {originalFrameSize && <p>Size: {originalFrameSize}</p>}
            </div>
            <div className="compressed">
              <h2>Compressed First Frame:</h2>
              <img src={compressedImageUrl} alt="Compressed first frame" className="thumbnail" />
              {compressedImageSize && <p>Size: {compressedImageSize}</p>}
              {sizeReductionPercentage !== null && (
                <p>Size reduction: {sizeReductionPercentage}%</p>
              )}
            </div>
          </div>
        )}
        {sizeReductionPercentage !== null && estimatedVideoSize && (
          <div className="estimation">
            <h3>🎬 Video Compression Magic ✨</h3>
            <p>Abracadabra! Based on our frame-shrinking wizardry, we predict your video will slim down to a svelte <strong>{estimatedVideoSize}</strong>.</p>
            <p>🔮 Remember, this is our crystal ball's best guess - reality might have a few tricks up its sleeve!</p>
          </div>
        )}
        {compressedVideoUrl && (
          <div className="video-comparison">
            <h2>Compressed Video:</h2>
            <video src={compressedVideoUrl} controls className="compressed-video" />
            <div className="size-comparison">
              <p>Original Size: <strong>{fileSize}</strong></p> 
              {compressedVideoSize && <p style={{ marginLeft: '10px' }}>{" ---> "} Compressed Size: <strong>{compressedVideoSize}</strong></p>}
            </div>
          </div>
        )}
        <canvas ref={canvasRef} style={{ display: 'none' }} />
        {isFrameCompressing && <p className="loading">Compressing frame... Please wait.</p>}
        {isVideoCompressing && <p className="loading">Compressing video... This may take a while.</p>}
      </header>
    </div>
  );
}

export default App;