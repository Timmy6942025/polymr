declare module "*.css" {
  const content: typeof import("*.css")
}

declare module "*.json" {
  const content: any
}

declare module "*.svg" {
  const content: React.FC<React.SVGProps<SVGSVGElement>>
  const namespace: "http://www.w3.org/2000/svg"
}
