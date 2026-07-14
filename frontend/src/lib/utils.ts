import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const glassSurface =
  "bg-[#131926] border border-[#1E3456] shadow-2xl hover:bg-[#1c2538] hover:border-cyan-400/40 transition-all duration-300";

export const glassSurfaceStatic =
  "bg-[#131926] border border-[#1E3456] shadow-2xl";
