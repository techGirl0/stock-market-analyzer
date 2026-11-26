import { StockDashboard } from "./StockDashboard";

interface StockPageProps {
  params: Promise<{ symbol: string }>;
}

export default async function StockPage({ params }: StockPageProps) {
  const { symbol } = await params;
  return <StockDashboard symbol={decodeURIComponent(symbol).toUpperCase()} />;
}
