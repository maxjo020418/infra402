import type { Metadata } from "next";
import dynamic from "next/dynamic";
import "./globals.css";

const Web3ModalProvider = dynamic(
  () => import("@/contexts/Web3ModalProvider").then((mod) => mod.Web3ModalProvider),
  {
    ssr: false,
  }
);

export const metadata: Metadata = {
  title: "Infra402",
  description: "Lease infrastructure with x402 payments",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Web3ModalProvider>{children}</Web3ModalProvider>
      </body>
    </html>
  );
}
