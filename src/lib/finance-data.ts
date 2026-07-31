// Centralized dummy data for MoneyScope. All amounts in INR.

export type UpiApp = "GPay" | "PhonePe" | "Paytm" | "BHIM" | "CRED" | "Amazon Pay";
export type Category =
  | "Food & Dining"
  | "Groceries"
  | "Transport"
  | "Shopping"
  | "Bills & Utilities"
  | "Entertainment"
  | "Health"
  | "Rent"
  | "Investments"
  | "Income"
  | "Transfer"
  | "Other";

export interface Transaction {
  id: string;
  date: string; // ISO
  merchant: string;
  category: Category;
  app: UpiApp;
  amount: number; // negative = expense, positive = income
  note?: string;
}

export const CATEGORY_META: Record<Category, { color: string; emoji: string }> = {
  "Food & Dining":   { color: "var(--chart-1)", emoji: "🍜" },
  Groceries:         { color: "var(--chart-2)", emoji: "🛒" },
  Transport:         { color: "var(--chart-3)", emoji: "🚖" },
  Shopping:          { color: "var(--chart-4)", emoji: "🛍️" },
  "Bills & Utilities":{ color: "var(--chart-5)", emoji: "💡" },
  Entertainment:     { color: "var(--chart-4)", emoji: "🎬" },
  Health:            { color: "var(--chart-1)", emoji: "🩺" },
  Rent:              { color: "var(--chart-2)", emoji: "🏠" },
  Investments:       { color: "var(--chart-2)", emoji: "📈" },
  Income:            { color: "var(--chart-1)", emoji: "💰" },
  Transfer:          { color: "var(--chart-3)", emoji: "🔁" },
  Other:             { color: "var(--chart-5)", emoji: "•" },
};

export const APP_META: Record<UpiApp, { color: string }> = {
  GPay: { color: "#4285F4" },
  PhonePe: { color: "#5F259F" },
  Paytm: { color: "#00BAF2" },
  BHIM: { color: "#F47216" },
  CRED: { color: "#0E0E10" },
  "Amazon Pay": { color: "#FF9900" },
};

const today = new Date();
function daysAgo(d: number, h = 10, m = 0) {
  const dt = new Date(today);
  dt.setDate(dt.getDate() - d);
  dt.setHours(h, m, 0, 0);
  return dt.toISOString();
}

export const transactions: Transaction[] = [
  { id: "t1",  date: daysAgo(0, 9, 12),  merchant: "Blue Tokai Coffee", category: "Food & Dining", app: "GPay",    amount: -340 },
  { id: "t2",  date: daysAgo(0, 13, 5),  merchant: "Uber",              category: "Transport",     app: "PhonePe", amount: -218 },
  { id: "t3",  date: daysAgo(0, 20, 30), merchant: "Zomato",            category: "Food & Dining", app: "Paytm",   amount: -612 },
  { id: "t4",  date: daysAgo(1, 8, 0),   merchant: "BigBasket",         category: "Groceries",     app: "GPay",    amount: -1840 },
  { id: "t5",  date: daysAgo(1, 19, 0),  merchant: "BookMyShow",        category: "Entertainment", app: "CRED",    amount: -780 },
  { id: "t6",  date: daysAgo(2, 11, 0),  merchant: "Airtel Postpaid",   category: "Bills & Utilities", app: "PhonePe", amount: -799 },
  { id: "t7",  date: daysAgo(3, 10, 0),  merchant: "Amazon",            category: "Shopping",      app: "Amazon Pay", amount: -2499 },
  { id: "t8",  date: daysAgo(3, 21, 0),  merchant: "Swiggy",            category: "Food & Dining", app: "GPay",    amount: -456 },
  { id: "t9",  date: daysAgo(4, 9, 0),   merchant: "Metro Card Recharge",category:"Transport",     app: "Paytm",   amount: -500 },
  { id: "t10", date: daysAgo(5, 12, 0),  merchant: "Apollo Pharmacy",   category: "Health",        app: "PhonePe", amount: -642 },
  { id: "t11", date: daysAgo(6, 11, 0),  merchant: "Netflix",           category: "Entertainment", app: "CRED",    amount: -649 },
  { id: "t12", date: daysAgo(7, 18, 0),  merchant: "Salary — Acme Co.", category: "Income",        app: "GPay",    amount: 124000 },
  { id: "t13", date: daysAgo(8, 11, 0),  merchant: "Zepto",             category: "Groceries",     app: "GPay",    amount: -540 },
  { id: "t14", date: daysAgo(9, 14, 0),  merchant: "Petrol — HP",       category: "Transport",     app: "PhonePe", amount: -1500 },
  { id: "t15", date: daysAgo(10, 19, 0), merchant: "Starbucks",         category: "Food & Dining", app: "GPay",    amount: -485 },
  { id: "t16", date: daysAgo(11, 10, 0), merchant: "Electricity Bill",  category: "Bills & Utilities", app: "Paytm", amount: -2240 },
  { id: "t17", date: daysAgo(12, 9, 0),  merchant: "Rent — Landlord",   category: "Rent",          app: "BHIM",    amount: -28000 },
  { id: "t18", date: daysAgo(13, 13, 0), merchant: "Myntra",            category: "Shopping",      app: "PhonePe", amount: -3299 },
  { id: "t19", date: daysAgo(14, 8, 0),  merchant: "SIP — Nifty 50",    category: "Investments",   app: "GPay",    amount: -10000 },
  { id: "t20", date: daysAgo(15, 20, 0), merchant: "Dominos",           category: "Food & Dining", app: "Paytm",   amount: -740 },
  { id: "t21", date: daysAgo(17, 10, 0), merchant: "Ola",               category: "Transport",     app: "PhonePe", amount: -312 },
  { id: "t22", date: daysAgo(19, 12, 0), merchant: "DMart",             category: "Groceries",     app: "GPay",    amount: -2120 },
  { id: "t23", date: daysAgo(21, 9, 0),  merchant: "Spotify",           category: "Entertainment", app: "CRED",    amount: -119 },
  { id: "t24", date: daysAgo(23, 14, 0), merchant: "Cult.fit",          category: "Health",        app: "PhonePe", amount: -1499 },
  { id: "t25", date: daysAgo(25, 10, 0), merchant: "SIP — Flexi Cap",   category: "Investments",   app: "GPay",    amount: -7500 },
  { id: "t26", date: daysAgo(27, 16, 0), merchant: "Croma",             category: "Shopping",      app: "Amazon Pay", amount: -8499 },
];

export const goals = [
  { id: "g1", name: "Emergency Fund",  target: 200000, saved: 142000, deadline: "Dec 2026", color: "var(--chart-1)", icon: "🛟" },
  { id: "g2", name: "Japan Trip",      target: 180000, saved:  64000, deadline: "Mar 2027", color: "var(--chart-2)", icon: "🗾" },
  { id: "g3", name: "New MacBook",     target: 160000, saved:  98000, deadline: "Aug 2026", color: "var(--chart-3)", icon: "💻" },
  { id: "g4", name: "Down Payment",    target: 1500000, saved: 412000, deadline: "2028",    color: "var(--chart-4)", icon: "🏡" },
];

export const investments = [
  { id: "i1", name: "Nifty 50 Index Fund", type: "Mutual Fund", invested: 120000, value: 148200, change: 23.5 },
  { id: "i2", name: "Flexi Cap Fund",       type: "Mutual Fund", invested: 90000,  value: 102600, change: 14.0 },
  { id: "i3", name: "HDFC Bank",            type: "Stock",       invested: 48000,  value: 53760,  change: 12.0 },
  { id: "i4", name: "Gold ETF",             type: "ETF",         invested: 30000,  value: 33900,  change: 13.0 },
  { id: "i5", name: "Liquid Fund",          type: "Debt",        invested: 60000,  value: 62400,  change: 4.0 },
  { id: "i6", name: "Crypto Basket",        type: "Crypto",      invested: 25000,  value: 21500,  change: -14.0 },
];

export const newsItems = [
  { id: "n1", title: "RBI holds repo rate at 6.50% for the seventh time",       source: "Mint",         time: "2h",  tag: "Policy",      hot: true },
  { id: "n2", title: "Nifty 50 closes at a record high, IT stocks lead rally",  source: "Bloomberg",    time: "3h",  tag: "Markets",     hot: true },
  { id: "n3", title: "New tax regime: deductions you can still claim in FY26",  source: "Economic Times", time: "5h", tag: "Tax" },
  { id: "n4", title: "UPI transactions cross 17 billion in a single month",     source: "Reuters",      time: "7h",  tag: "Payments" },
  { id: "n5", title: "Gold prices steady ahead of Fed minutes",                 source: "CNBC",         time: "9h",  tag: "Commodities" },
  { id: "n6", title: "How to build an emergency fund in 12 months",             source: "MoneyScope",   time: "1d",  tag: "Guide" },
  { id: "n7", title: "SIP inflows hit fresh high of ₹23,300 cr",                source: "Livemint",     time: "1d",  tag: "Mutual Funds" },
];

export const alerts = [
  { id: "a1", type: "warning" as const, title: "Food & Dining over budget",  body: "You've spent 92% of your dining budget with 9 days left.", icon: "🍽️" },
  { id: "a2", type: "info" as const,    title: "Credit card bill due",       body: "HDFC card payment of ₹18,420 due in 3 days.",              icon: "💳" },
  { id: "a3", type: "success" as const, title: "Goal milestone reached",     body: "You crossed 70% of 'Emergency Fund'. Keep going!",         icon: "🎯" },
];

// Helpers
export const inr = (n: number) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);

export const inrShort = (n: number) => {
  const a = Math.abs(n);
  if (a >= 1e7) return `₹${(n/1e7).toFixed(1)}Cr`;
  if (a >= 1e5) return `₹${(n/1e5).toFixed(1)}L`;
  if (a >= 1e3) return `₹${(n/1e3).toFixed(1)}k`;
  return `₹${n}`;
};

const startOfDay = (d: Date) => { const x = new Date(d); x.setHours(0,0,0,0); return x; };
const sameDay = (a: Date, b: Date) => startOfDay(a).getTime() === startOfDay(b).getTime();
const sameMonth = (a: Date, b: Date) => a.getMonth() === b.getMonth() && a.getFullYear() === b.getFullYear();

export function getSummary() {
  const now = new Date();
  const expenses = transactions.filter(t => t.amount < 0);
  const income = transactions.filter(t => t.amount > 0);

  const todaySpent = expenses.filter(t => sameDay(new Date(t.date), now)).reduce((s,t) => s + -t.amount, 0);
  const monthSpent = expenses.filter(t => sameMonth(new Date(t.date), now)).reduce((s,t) => s + -t.amount, 0);
  const monthIncome = income.filter(t => sameMonth(new Date(t.date), now)).reduce((s,t) => s + t.amount, 0);

  const monthlyBudget = 70000;
  const remaining = Math.max(monthlyBudget - monthSpent, 0);
  const daysLeft = Math.max(1, new Date(now.getFullYear(), now.getMonth()+1, 0).getDate() - now.getDate());
  const safeToSpend = Math.round(remaining / daysLeft);

  // Category breakdown (this month)
  const byCat = new Map<Category, number>();
  expenses.filter(t => sameMonth(new Date(t.date), now)).forEach(t => {
    byCat.set(t.category, (byCat.get(t.category) ?? 0) + -t.amount);
  });
  const categoryBreakdown = Array.from(byCat.entries())
    .map(([name, value]) => ({ name, value, color: CATEGORY_META[name].color }))
    .sort((a,b) => b.value - a.value);

  // 14-day trend
  const trend: { day: string; spend: number }[] = [];
  for (let i = 13; i >= 0; i--) {
    const d = new Date(now); d.setDate(d.getDate() - i);
    const spend = expenses.filter(t => sameDay(new Date(t.date), d)).reduce((s,t) => s + -t.amount, 0);
    trend.push({ day: d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" }), spend });
  }

  // Investments
  const invInvested = investments.reduce((s,i) => s + i.invested, 0);
  const invValue = investments.reduce((s,i) => s + i.value, 0);
  const invChangePct = ((invValue - invInvested) / invInvested) * 100;

  // Health score (out of 100)
  const savingsRate = monthIncome > 0 ? (monthIncome - monthSpent) / monthIncome : 0;
  const budgetUtil = Math.min(monthSpent / monthlyBudget, 1.2);
  const goalAvg = goals.reduce((s,g) => s + g.saved/g.target, 0) / goals.length;
  const healthScore = Math.round(
    Math.max(0, Math.min(100,
      40 * Math.max(0, savingsRate) + 30 * (1 - Math.min(budgetUtil, 1)) + 20 * goalAvg + 10 * (invChangePct > 0 ? 1 : 0.4)
    ))
  );

  return {
    todaySpent, monthSpent, monthIncome, monthlyBudget, remaining, safeToSpend,
    categoryBreakdown, trend, invInvested, invValue, invChangePct, healthScore,
  };
}
