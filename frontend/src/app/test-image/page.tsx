import Image from "next/image";

export default function TestImagePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <h1 className="text-2xl font-bold mb-4">Image Test Page</h1>

      <div className="border p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Normal Image Tag:</h2>
        {/* <img
          src="/ambi-alert.png"
          alt="Ambi Alert Logo (normal img)"
          className="h-24 w-24 object-contain"
        /> */}
      </div>

      <div className="border p-4 rounded-lg mt-4">
        <h2 className="text-lg font-semibold mb-2">Next.js Image Component:</h2>
        <div className="relative h-24 w-24">
          <Image
            src="/ambi-alert.png"
            alt="Ambi Alert Logo (Next.js)"
            fill
            className="object-contain"
          />
        </div>
      </div>

      <div className="mt-8">
        <p className="text-sm text-gray-600">
          If both images are visible, the image is properly accessible.
        </p>
        <p className="text-sm text-gray-600">
          If not, there might be an issue with the file path or Next.js image
          configuration.
        </p>
      </div>
    </div>
  );
}
