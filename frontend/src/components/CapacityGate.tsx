import { useEffect, useState, ReactNode } from "react";
import { Loader2 } from "lucide-react";

interface CapacityGateProps {
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * CapacityGate - Controls access based on user capacity limits
 *
 * Fetches available slots from the public API and conditionally renders:
 * - children: When capacity is available (slots > 0)
 * - fallback: When at capacity (slots === 0)
 *
 * Fallback should be provided (e.g., redirect to /waitlist).
 */
export function CapacityGate({ children, fallback }: CapacityGateProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [availableSlots, setAvailableSlots] = useState<number | null>(null);

  useEffect(() => {
    const fetchCapacity = async () => {
      try {
        const apiUrl = window.CONFIG?.apiUrl || import.meta.env.VITE_API_BASE_URL;
        if (!apiUrl) {
          console.error("API URL is not set");
          setIsLoading(false);
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
      } finally {
        setIsLoading(false);
      }
    };

    fetchCapacity();
  }, []);

  // Show loading state while checking capacity
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // If we have slots available (or couldn't determine), allow access
  if (availableSlots === null || availableSlots > 0) {
    return <>{children}</>;
  }

  // At capacity - show fallback
  return <>{fallback}</>;
}
