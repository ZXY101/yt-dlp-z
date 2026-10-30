import {
  Cookie,
  Download,
  ListVideo,
  type LucideIcon,
  Rss,
  Settings,
  SlidersHorizontal,
} from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Download", icon: Download },
  { to: "/queue", label: "Queue", icon: ListVideo },
  { to: "/subscriptions", label: "Subscriptions", icon: Rss },
  { to: "/presets", label: "Presets", icon: SlidersHorizontal },
  { to: "/cookies", label: "Cookies", icon: Cookie },
  { to: "/settings", label: "Settings", icon: Settings },
];
