import { Download, ListVideo, type LucideIcon } from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Download", icon: Download },
  { to: "/queue", label: "Queue", icon: ListVideo },
];
