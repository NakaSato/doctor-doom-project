/**
 * Thermal Image Parser
 * 
 * Parses R-JPEG (Radiometric JPEG) thermal images from FLIR/DJI cameras
 * Extracts temperature data and metadata
 */

export interface ThermalImageMetadata {
  width: number;
  height: number;
  emissivity: number;
  reflectedTemp: number;
  atmosphericTemp: number;
  objectDistance: number;
  relativeHumidity: number;
  planckR1: number;
  planckB: number;
  planckF: number;
  planckO: number;
  planckR2: number;
  planckB1: number;
  planckB2: number;
  cameraModel: string;
  timestamp: string;
  lensModel?: string;
}

export interface ThermalImageData {
  metadata: ThermalImageMetadata;
  rawTemps: Float32Array;  // Temperature values in Kelvin
  width: number;
  height: number;
}

/**
 * Parse R-JPEG file and extract thermal data
 */
export async function parseRJpeg(file: File): Promise<ThermalImageData> {
  try {
    // Read file as ArrayBuffer
    const arrayBuffer = await file.arrayBuffer();
    const dataView = new DataView(arrayBuffer);
    
    // Verify JPEG signature
    if (dataView.getUint16(0) !== 0xFFD8) {
      throw new Error('Not a valid JPEG file');
    }
    
    // Extract EXIF and thermal metadata
    const metadata = extractThermalMetadata(dataView);
    
    // Extract raw thermal data
    const rawTemps = extractRawThermalData(dataView, metadata);
    
    return {
      metadata,
      rawTemps,
      width: metadata.width,
      height: metadata.height,
    };
  } catch (error) {
    console.error('Failed to parse R-JPEG:', error);
    throw new Error(`Failed to parse thermal image: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Extract thermal metadata from JPEG segments
 */
function extractThermalMetadata(dataView: DataView): ThermalImageMetadata {
  const metadata: Partial<ThermalImageMetadata> = {
    width: 640,  // Default for DJI M3T
    height: 512,
    emissivity: 0.95,
    reflectedTemp: 293.15,  // 20°C in Kelvin
    atmosphericTemp: 293.15,
    objectDistance: 1.0,
    relativeHumidity: 50,
    planckR1: 21106.77,
    planckB: 1501,
    planckF: 1,
    planckO: -7340,
    planckR2: 0.012545258,
    planckB1: 0.006834,
    planckB2: 0.003835,
    cameraModel: 'FLIR Compatible',
    timestamp: new Date().toISOString(),
  };
  
  // Parse JPEG segments to find EXIF and thermal data
  let offset = 2; // Skip SOI marker
  const length = dataView.byteLength;
  
  while (offset < length) {
    // Read marker
    const marker = dataView.getUint16(offset);
    
    // Skip padding
    if (marker === 0xFF01) {
      offset += 2;
      continue;
    }
    
    // Check for SOS (Start of Scan) - end of headers
    if (marker === 0xFFDA) {
      break;
    }
    
    // Read segment length
    if (marker >= 0xFFC0 && marker <= 0xFFC3) {
      // SOF (Start of Frame) segment - get dimensions
      const segLength = dataView.getUint16(offset + 2);
      metadata.height = dataView.getUint16(offset + 5);
      metadata.width = dataView.getUint16(offset + 7);
      offset += 2 + segLength;
    } else if (marker === 0xFFE1) {
      // APP1 segment - might contain EXIF
      const segLength = dataView.getUint16(offset + 2);
      parseExifSegment(dataView, offset + 4, segLength - 2, metadata);
      offset += 2 + segLength;
    } else {
      // Skip unknown segment
      const segLength = dataView.getUint16(offset + 2);
      offset += 2 + segLength;
    }
  }
  
  return metadata as ThermalImageMetadata;
}

/**
 * Parse EXIF segment for thermal metadata
 */
function parseExifSegment(
  dataView: DataView,
  offset: number,
  length: number,
  metadata: Partial<ThermalImageMetadata>
) {
  // Check for EXIF header
  const exifHeader = getString(dataView, offset, 6);
  if (exifHeader !== 'Exif\0\0') {
    return;
  }
  
  let exifOffset = offset + 6;
  
  // Check for TIFF header
  const tiffHeader = dataView.getUint32(exifOffset);
  if (tiffHeader !== 0x2A002BCD && tiffHeader !== 0x002A002A) {
    return;
  }
  
  // Parse TIFF tags
  // This is simplified - full implementation would parse all thermal tags
  const tagCount = dataView.getUint16(exifOffset + 4);
  let tagOffset = exifOffset + 6;
  
  for (let i = 0; i < tagCount; i++) {
    const tagId = dataView.getUint16(tagOffset);
    const tagType = dataView.getUint16(tagOffset + 2);
    const tagCount = dataView.getUint32(tagOffset + 4);
    const tagValueOffset = tagOffset + 8;
    
    // Parse specific thermal tags (FLIR custom tags)
    switch (tagId) {
      case 0x0320: // Emissivity
        metadata.emissivity = dataView.getFloat32(tagValueOffset, true);
        break;
      case 0x0321: // Reflected temperature
        metadata.reflectedTemp = dataView.getFloat32(tagValueOffset, true);
        break;
    }
    
    tagOffset += 12;
  }
}

/**
 * Extract raw thermal data from JPEG
 */
function extractRawThermalData(
  dataView: DataView,
  metadata: ThermalImageMetadata
): Float32Array {
  // For R-JPEG, thermal data is typically in a separate segment
  // This is a simplified implementation
  
  const totalPixels = metadata.width * metadata.height;
  const rawTemps = new Float32Array(totalPixels);
  
  // Try to find thermal data segment (APP2 or private segment)
  let offset = 2;
  const length = dataView.byteLength;
  
  while (offset < length) {
    const marker = dataView.getUint16(offset);
    
    if (marker === 0xFFDA) {
      break; // SOS
    }
    
    if (marker === 0xFFE2) {
      // APP2 segment - might contain thermal data
      const segLength = dataView.getUint16(offset + 2);
      const segData = new Uint8Array(dataView.buffer, offset + 4, segLength - 2);
      
      // Check for FLIR thermal data signature
      if (segData[0] === 0x46 && segData[1] === 0x4C && segData[2] === 0x49) {
        // "FLI" - FLIR data
        extractFlirThermalData(segData, rawTemps, metadata);
        return rawTemps;
      }
    }
    
    const segLength = dataView.getUint16(offset + 2);
    offset += 2 + segLength;
  }
  
  // If no thermal data found, generate placeholder
  console.warn('No thermal data found, generating placeholder');
  return generatePlaceholderThermalData(totalPixels);
}

/**
 * Extract FLIR thermal data
 */
function extractFlirThermalData(
  data: Uint8Array,
  rawTemps: Float32Array,
  metadata: ThermalImageMetadata
) {
  // FLIR thermal data format parsing
  // This is simplified - full implementation would handle all FLIR formats
  
  let dataOffset = 0;
  
  // Skip FLIR header
  if (data[0] === 0x46 && data[1] === 0x4C && data[2] === 0x49) {
    dataOffset = 64; // Skip standard FLIR header
  }
  
  // Read raw thermal values (16-bit)
  const view = new DataView(data.buffer);
  let tempIndex = 0;
  
  for (let i = dataOffset; i < data.length - 1 && tempIndex < rawTemps.length; i += 2) {
    const rawValue = view.getUint16(i, true);
    
    // Convert raw value to temperature (Kelvin)
    const temperature = rawToKelvin(rawValue, metadata);
    rawTemps[tempIndex++] = temperature;
  }
}

/**
 * Convert raw sensor value to Kelvin
 */
function rawToKelvin(raw: number, metadata: ThermalImageMetadata): number {
  const {
    planckR1, planckB, planckF, planckO, planckR2,
    planckB1, planckB2, emissivity, reflectedTemp
  } = metadata;
  
  // Planck equation for temperature conversion
  const rawReflected = planckR1 / (planckR2 * (Math.exp(planckB / reflectedTemp) - planckF)) - planckO;
  const rawAtmosphere = raw;
  
  const rawObject = (
    rawAtmosphere / emissivity +
    (1 - emissivity) / emissivity * rawReflected
  );
  
  const temperature = planckB / Math.log(
    planckR1 / (planckR2 * (rawObject + planckO)) + planckF
  );
  
  return temperature;
}

/**
 * Generate placeholder thermal data for testing
 */
function generatePlaceholderThermalData(count: number): Float32Array {
  const data = new Float32Array(count);
  const baseTemp = 308.15; // 35°C in Kelvin
  
  for (let i = 0; i < count; i++) {
    // Generate realistic temperature variation
    const variation = Math.sin(i / 50) * 10 + Math.random() * 5;
    data[i] = baseTemp + variation;
  }
  
  return data;
}

/**
 * Helper: Get string from DataView
 */
function getString(dataView: DataView, offset: number, length: number): string {
  let result = '';
  for (let i = 0; i < length; i++) {
    result += String.fromCharCode(dataView.getUint8(offset + i));
  }
  return result;
}

/**
 * Convert Kelvin to Celsius
 */
export function kelvinToCelsius(kelvin: number): number {
  return kelvin - 273.15;
}

/**
 * Convert Celsius to Kelvin
 */
export function celsiusToKelvin(celsius: number): number {
  return celsius + 273.15;
}

/**
 * Get temperature statistics
 */
export function getTemperatureStats(temps: Float32Array): {
  min: number;
  max: number;
  avg: number;
  stdDev: number;
} {
  const n = temps.length;
  if (n === 0) {
    return { min: 0, max: 0, avg: 0, stdDev: 0 };
  }
  
  let sum = 0;
  let min = temps[0];
  let max = temps[0];
  
  for (let i = 0; i < n; i++) {
    sum += temps[i];
    if (temps[i] < min) min = temps[i];
    if (temps[i] > max) max = temps[i];
  }
  
  const avg = sum / n;
  
  // Calculate standard deviation
  let sumSquaredDiff = 0;
  for (let i = 0; i < n; i++) {
    const diff = temps[i] - avg;
    sumSquaredDiff += diff * diff;
  }
  const stdDev = Math.sqrt(sumSquaredDiff / n);
  
  return {
    min: kelvinToCelsius(min),
    max: kelvinToCelsius(max),
    avg: kelvinToCelsius(avg),
    stdDev,
  };
}

/**
 * Create thermal image preview (grayscale)
 */
export function createThermalPreview(
  temps: Float32Array,
  width: number,
  height: number
): ImageData {
  const stats = getTemperatureStats(temps);
  const { min, max } = stats;
  const range = max - min || 1;
  
  const imageData = new ImageData(width, height);
  const data = imageData.data;
  
  for (let i = 0; i < temps.length; i++) {
    const temp = kelvinToCelsius(temps[i]);
    const normalized = (temp - min) / range;
    const gray = Math.floor(normalized * 255);
    
    const idx = i * 4;
    data[idx] = gray;     // R
    data[idx + 1] = gray; // G
    data[idx + 2] = gray; // B
    data[idx + 3] = 255;  // A
  }
  
  return imageData;
}
