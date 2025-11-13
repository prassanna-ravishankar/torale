import { useEffect, useState } from "react";

export function CapacityBadge() {
  const [availableSlots, setAvailableSlots] = useState<number | null>(null);
  const isFull = availableSlots === 0;

  useEffect(() => {
    const fetchCapacity = async () => {
      try {
        const apiUrl = window.CONFIG?.apiUrl || import.meta.env.VITE_API_BASE_URL;
        if (!apiUrl) {
          console.error("API URL is not set");
          return;
        }
        const response = await fetch(`${apiUrl}/public/stats`);
        if (response.ok) {
          const data = await response.json();
          if (typeof data?.capacity?.available_slots === "number") {
            setAvailableSlots(data.capacity.available_slots);
          }
        }
      } catch (error) {
        console.error("Failed to fetch capacity stats:", error);
      }
    };

    fetchCapacity();
  }, []);

  return (
    <div className="inline-block bg-black text-white px-4 py-2 font-mono text-sm mb-4">
      {isFull
        ? "[ We're at capacity - join the waitlist! ]"
        : availableSlots !== null && availableSlots > 0
        ? `[ Free for ${availableSlots} more user${availableSlots === 1 ? "" : "s"} till I figure out what this is used for ]`
        : "[ Free till I figure out what this is used for ]"}
    </div>
  );
}
