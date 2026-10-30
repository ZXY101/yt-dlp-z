import { CirclePlus, LayoutDashboard, ListVideo, type LucideIcon } from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/download", label: "New download", icon: CirclePlus },
  { to: "/queue", label: "Queue", icon: ListVideo },
];
