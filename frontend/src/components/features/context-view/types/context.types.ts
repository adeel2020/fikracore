export interface GraphNode {
  id: string;
  label: string;
  type:
    | "Intent"
    | "Service"
    | "Platform"
    | "Precondition"
    | "Error"
    | "Channel"
    | "CustomerProfile"
    | "AppType"
    | "Hub"
    | "FAQ";
  x?: number;
  y?: number;
  isHub?: boolean;
  hubType?: string;
  symbol?: "+" | "-";
  url?: string;
  prechecks?: string[];
  target?: string;
  prohibited?: string[];
}

export interface GraphLink {
  source: string | any;
  target: string | any;
  label: string;
  isHubLink?: boolean;
}

export interface ThemeConfig {
  id: string;
  name: string;
  isDark: boolean;
  gridBackground: string;
  inactiveLinkColor: string;
  inactiveNodeAlpha: number;
  nodeColors: Record<string, string>;
  labelTextColor: string;
  labelTextBackground: string;
  labelTextBorder: string;
}
