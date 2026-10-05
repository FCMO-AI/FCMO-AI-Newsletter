// Canvas removes input EXIF/GPS but Chromium adds its own ICC profile. Remove
// metadata chunks from the encoded container; keep compressed pixels untouched.
export async function stripWebpMetadata (blob) {
  const bytes = new Uint8Array(await blob.arrayBuffer()); const view = new DataView(bytes.buffer)
  const ascii = (start, length) => String.fromCharCode(...bytes.subarray(start, start + length))
  if (bytes.length < 20 || ascii(0, 4) !== 'RIFF' || ascii(8, 4) !== 'WEBP' || view.getUint32(4, true) !== bytes.length - 8) throw new Error('Invalid WebP')
  const chunks = []; let pos = 12
  while (pos < bytes.length) {
    if (pos + 8 > bytes.length) throw new Error('Incomplete WebP')
    const size = view.getUint32(pos + 4, true); const end = pos + 8 + size + (size % 2)
    if (end > bytes.length) throw new Error('Incomplete WebP')
    const kind = ascii(pos, 4)
    if (!['EXIF', 'XMP ', 'ICCP'].includes(kind)) {
      const chunk = bytes.slice(pos, end)
      if (kind === 'VP8X') { if (size !== 10) throw new Error('Invalid WebP'); chunk[8] &= ~0x2c }
      chunks.push(chunk)
    }
    pos = end
  }
  const length = 12 + chunks.reduce((n, c) => n + c.length, 0)
  const result = new Uint8Array(length); result.set(bytes.subarray(0, 12))
  new DataView(result.buffer).setUint32(4, length - 8, true)
  pos = 12; for (const chunk of chunks) { result.set(chunk, pos); pos += chunk.length }
  return new Blob([result], { type: 'image/webp' })
}
