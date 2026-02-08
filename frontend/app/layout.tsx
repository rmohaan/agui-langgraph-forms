import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AG-UI LangGraph",
  description: "CopilotKit + AG-UI + LangGraph demo",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
