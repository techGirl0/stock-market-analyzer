interface StockPageProps {
  params: Promise<{ symbol: string }>;
}

export default async function StockPage({ params }: StockPageProps) {
  const { symbol } = await params;

  return (
    <div>
      <h1>{symbol.toUpperCase()}</h1>
      {/* SCRUM-105: Stock Dashboard — implement stock detail UI here */}
    </div>
  );
}
