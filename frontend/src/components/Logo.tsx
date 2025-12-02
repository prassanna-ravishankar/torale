import React from "react";
import { cn } from "@/lib/utils";

interface LogoProps {
    className?: string;
    showText?: boolean;
    textClassName?: string;
}

export const Logo: React.FC<LogoProps> = ({
    className,
    showText = true,
    textClassName
}) => {
    return (
        <div className={cn("flex items-center gap-3 group select-none cursor-pointer", className)}>
            <div className="relative w-8 h-8 flex items-center justify-center">
                <svg
                    viewBox="0 0 32 32"
                    className="w-full h-full transition-colors duration-200 fill-zinc-900 group-hover:fill-[hsl(10,90%,55%)]"
                    xmlns="http://www.w3.org/2000/svg"
                >
                    {/* Top bar - split and shifted */}
                    <path d="M2 6H16V12H2Z" />
                    <path d="M18 4H30V10H18Z" />

                    {/* Vertical stem - glitch cut */}
                    <path d="M13 12H19V20H13Z" />
                    <path d="M15 22H21V30H15Z" />

                    {/* Digital noise particles */}
                    <rect x="22" y="14" width="3" height="3" />
                    <rect x="8" y="24" width="2" height="2" />
                </svg>
            </div>

            {showText && (
                <span className={cn(
                    "font-grotesk font-bold text-xl tracking-tight text-zinc-900",
                    textClassName
                )}>
                    torale
                </span>
            )}
        </div>
    );
};
