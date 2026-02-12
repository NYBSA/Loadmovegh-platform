"use client";

import { useState } from "react";

const faqs = [
  {
    category: "Getting Started",
    items: [
      {
        q: "What is LoadMoveGH?",
        a: "LoadMoveGH is Ghana's leading AI-powered freight marketplace. We connect shippers who need to move goods with verified courier drivers across all 16 regions of Ghana. Think of it as a matchmaking platform for freight — shippers post loads, couriers bid on them, and our AI helps ensure fair pricing and reliable delivery.",
      },
      {
        q: "How do I sign up?",
        a: "Visit www.loadmovegh.com and scroll to the sign-up section. Choose your role (Shipper or Courier), fill in your details, and create your account in under a minute. It's completely free to join.",
      },
      {
        q: "Is LoadMoveGH free to use?",
        a: "Yes, signing up and browsing the platform is completely free. We only charge a small commission on completed deliveries. Shippers pay the full bid amount, and the courier receives the payment minus our platform commission. See our Pricing page for current rates.",
      },
      {
        q: "What regions do you cover?",
        a: "LoadMoveGH covers all 16 regions of Ghana — from Greater Accra and Ashanti to Northern, Upper East, Upper West, Volta, Western, and every region in between. We're also expanding to cover cross-border routes to neighbouring countries.",
      },
      {
        q: "Do I need a smartphone to use LoadMoveGH?",
        a: "You can use LoadMoveGH on any device with a web browser — desktop, laptop, tablet, or smartphone. We also have a mobile app (coming soon on Google Play Store) for couriers and shippers who are always on the move.",
      },
    ],
  },
  {
    category: "For Shippers",
    items: [
      {
        q: "How do I post a load?",
        a: "After signing in to your shipper dashboard, click 'Post a Load'. Fill in the pickup location, delivery location, load description (weight, dimensions, type of goods), desired pickup date, and any special requirements (e.g., refrigeration, fragile items). Your load will be visible to all verified couriers immediately.",
      },
      {
        q: "How do I choose a courier?",
        a: "Once you post a load, couriers will submit bids with their proposed price. You can view each courier's profile, including their rating, vehicle type, completion rate, and past reviews. Our AI also ranks bids by value — considering price, reliability, and vehicle suitability. Accept the bid that best suits your needs.",
      },
      {
        q: "How does the escrow payment work?",
        a: "When you accept a bid, the agreed amount is transferred from your wallet into escrow — a secure holding account. The courier cannot access these funds until you confirm that the delivery has been completed successfully. This protects both parties.",
      },
      {
        q: "What if my goods are damaged during delivery?",
        a: "If goods are damaged, you can raise a dispute through the platform before confirming delivery. Both you and the courier can submit evidence (photos, descriptions). Our team will review the dispute within 7 business days. Escrow funds are held until the dispute is resolved. We strongly recommend insuring high-value goods independently.",
      },
      {
        q: "Can I cancel a load after posting?",
        a: "Yes, you can cancel a load before any bid is accepted at no cost. If you cancel after accepting a bid and funding escrow, a cancellation fee may apply depending on how far into the process the delivery is. The courier will be compensated fairly for any work already done.",
      },
    ],
  },
  {
    category: "For Couriers",
    items: [
      {
        q: "How do I find loads to transport?",
        a: "After signing in to your courier dashboard, you'll see the Available Loads Board with all current loads. You can filter by pickup location, delivery location, vehicle type required, distance, and price range. Our AI also suggests loads that match your location and vehicle.",
      },
      {
        q: "How do I submit a bid?",
        a: "Click on any load to see its full details, then click 'Place Bid'. Enter your proposed price (our AI will suggest a fair price range based on distance, load type, and market conditions). You can also add a message to the shipper explaining why you're the best choice.",
      },
      {
        q: "When do I get paid?",
        a: "You get paid as soon as the shipper confirms proof of delivery. The payment (minus platform commission) is credited to your LoadMoveGH wallet instantly. You can then withdraw to your Mobile Money account at any time.",
      },
      {
        q: "What vehicle types are accepted?",
        a: "We accept all commercial vehicle types: motorcycles, small vans, big vans, flatbed trucks, box trucks, container trucks, refrigerated trucks, tippers, and heavy trucks. Make sure to register your correct vehicle type so you receive relevant load matches.",
      },
      {
        q: "What if the shipper doesn't confirm delivery?",
        a: "If a shipper doesn't confirm delivery within 48 hours of your proof of delivery submission (GPS data, photos), the system will automatically review and release the escrow funds to you. You can also raise a dispute if needed.",
      },
      {
        q: "How does the AI load matching work?",
        a: "Our AI scores you based on your proximity to the pickup location, past acceptance and completion rates, vehicle suitability, pricing competitiveness, and overall reliability rating. Higher-scoring couriers appear first in shipper searches and receive priority load notifications.",
      },
    ],
  },
  {
    category: "Payments & Wallet",
    items: [
      {
        q: "What payment methods are supported?",
        a: "We support MTN Mobile Money, Vodafone Cash, and AirtelTigo Money. All deposits, escrow payments, and withdrawals are processed through these Mobile Money providers. No bank account is required.",
      },
      {
        q: "How do I deposit money into my wallet?",
        a: "Go to your Wallet page and click 'Deposit'. Enter the amount and your Mobile Money number. You'll receive a prompt on your phone to confirm the payment. Funds appear in your LoadMoveGH wallet within seconds.",
      },
      {
        q: "How do I withdraw money?",
        a: "Go to your Wallet page and click 'Withdraw'. Enter the amount (minimum GHS 5.00) and your Mobile Money number. Withdrawals are processed instantly in most cases. A small withdrawal fee applies (1%, minimum GHS 0.50, maximum GHS 10.00).",
      },
      {
        q: "Is my money safe in the LoadMoveGH wallet?",
        a: "Yes. Your funds are held securely and are always available for withdrawal. Escrow funds are held in a separate secure account and are only released upon delivery confirmation or dispute resolution. We use bank-grade encryption for all transactions.",
      },
      {
        q: "What are the transaction limits?",
        a: "Minimum deposit: GHS 1.00. Minimum withdrawal: GHS 5.00. Maximum single transaction: GHS 50,000. If you need higher limits for enterprise use, contact us at support@loadmovegh.com.",
      },
    ],
  },
  {
    category: "Safety & Trust",
    items: [
      {
        q: "How do you verify couriers?",
        a: "All couriers undergo verification including: Ghana Card or passport ID check, driver's licence validation, vehicle registration and roadworthiness certificate review, and insurance verification. Our AI fraud detection system continuously monitors for suspicious activity.",
      },
      {
        q: "How do you verify shippers?",
        a: "Shippers provide company details, business registration information, and contact details during signup. Our system verifies business information and monitors transaction patterns. Shippers must fund escrow before a courier begins any delivery, ensuring they can pay.",
      },
      {
        q: "What is your fraud detection system?",
        a: "Our AI-powered fraud detection system monitors all platform activity in real-time. It detects fake companies, suspicious bidding patterns, unusual pricing, repeated cancellations, and payment abuse. Users flagged for suspicious activity are reviewed and may have their accounts restricted or frozen.",
      },
      {
        q: "How does the rating system work?",
        a: "After each completed delivery, both the shipper and courier can rate each other (1-5 stars) and leave a review. Ratings are public and help build trust on the platform. Users with consistently low ratings may be flagged for review.",
      },
      {
        q: "Is my personal data safe?",
        a: "Yes. We comply with the Ghana Data Protection Act, 2012 (Act 843). All data is encrypted in transit (SSL/TLS) and at rest. We never sell your personal data to third-party advertisers. Read our full Privacy Policy for details.",
      },
    ],
  },
  {
    category: "AI Features",
    items: [
      {
        q: "How does AI pricing work?",
        a: "Our machine learning model analyses distance, fuel costs, load weight, urgency, regional demand, historical job prices, and current market conditions to suggest a fair bid price range. This helps couriers price competitively and shippers know what's reasonable.",
      },
      {
        q: "What is the AI assistant?",
        a: "The LoadMoveGH AI assistant is a built-in chatbot that helps you use the platform. Couriers can ask it to find loads, suggest pricing, calculate profit forecasts, and optimise routes. Shippers can get help posting loads, understanding bids, and tracking deliveries.",
      },
      {
        q: "How accurate are the AI price suggestions?",
        a: "Our AI is trained on thousands of real Ghanaian freight transactions and is continuously improving. Price suggestions are typically within 10-15% of the final agreed price. However, they are recommendations only — final pricing is always agreed between the shipper and courier.",
      },
    ],
  },
  {
    category: "Technical & Account",
    items: [
      {
        q: "I forgot my password. How do I reset it?",
        a: "Click 'Forgot password?' on the login form. Enter your registered email address and we'll send you a password reset link. If you registered with a phone number, you can reset via OTP. If you're still having trouble, contact support@loadmovegh.com.",
      },
      {
        q: "Can I change my role from shipper to courier (or vice versa)?",
        a: "Each account is registered for a specific role. If you need both shipper and courier access, you can create a separate account with a different email address for the other role. Contact support if you need help.",
      },
      {
        q: "What browsers are supported?",
        a: "LoadMoveGH works best on the latest versions of Google Chrome, Mozilla Firefox, Apple Safari, and Microsoft Edge. We recommend keeping your browser updated for the best experience and security.",
      },
      {
        q: "How do I delete my account?",
        a: "Email support@loadmovegh.com with your account deletion request. We'll process it within 7 business days. Please note that any outstanding escrow obligations must be settled before account closure. Transaction records are retained for 7 years as required by Ghana Revenue Authority regulations.",
      },
      {
        q: "How do I contact support?",
        a: "You can reach us by: Email at support@loadmovegh.com, Phone at +233 557 542 254 (Monday–Saturday, 8am–8pm GMT), or through the Help Centre on the platform. We aim to respond to all queries within 24 hours.",
      },
    ],
  },
];

export default function FAQsPage() {
  const [openIndex, setOpenIndex] = useState<string | null>(null);

  function toggle(id: string) {
    setOpenIndex(openIndex === id ? null : id);
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* ── Navbar ─────────────────────────────────── */}
      <nav className="sticky top-0 z-40 bg-white/80 backdrop-blur border-b border-gray-100">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
          <a href="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-green-600 to-emerald-500 flex items-center justify-center">
              <span className="text-sm font-black text-white">LM</span>
            </div>
            <span className="text-lg font-extrabold text-gray-900">
              LoadMove<span className="text-green-600">GH</span>
            </span>
          </a>
          <a href="/" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition">
            &larr; Back to Home
          </a>
        </div>
      </nav>

      {/* ── Header ─────────────────────────────────── */}
      <section className="py-12 sm:py-16 text-center">
        <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
          Frequently Asked Questions
        </h1>
        <p className="mt-3 text-gray-500 max-w-xl mx-auto text-sm sm:text-base">
          Everything you need to know about LoadMoveGH. Can&apos;t find what you&apos;re looking for?{" "}
          <a href="mailto:support@loadmovegh.com" className="text-green-600 hover:underline font-medium">
            Contact our support team
          </a>.
        </p>
      </section>

      {/* ── FAQ Sections ───────────────────────────── */}
      <div className="mx-auto max-w-3xl px-4 sm:px-6 pb-20 space-y-10">
        {faqs.map((section) => (
          <div key={section.category}>
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-green-600" />
              {section.category}
            </h2>
            <div className="space-y-2">
              {section.items.map((faq, i) => {
                const id = `${section.category}-${i}`;
                const isOpen = openIndex === id;
                return (
                  <div
                    key={id}
                    className={`rounded-xl border transition-all duration-200 ${
                      isOpen
                        ? "border-green-200 bg-green-50/50 shadow-sm"
                        : "border-gray-200 bg-white hover:border-gray-300"
                    }`}
                  >
                    <button
                      onClick={() => toggle(id)}
                      className="flex w-full items-start justify-between gap-4 px-5 py-4 text-left"
                    >
                      <span className={`text-sm font-semibold leading-snug ${isOpen ? "text-green-700" : "text-gray-900"}`}>
                        {faq.q}
                      </span>
                      <svg
                        className={`h-5 w-5 flex-shrink-0 transition-transform duration-200 ${
                          isOpen ? "rotate-180 text-green-600" : "text-gray-400"
                        }`}
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={2}
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                      </svg>
                    </button>
                    {isOpen && (
                      <div className="px-5 pb-4">
                        <p className="text-sm text-gray-600 leading-relaxed">{faq.a}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}

        {/* ── Still need help? ─────────────────────── */}
        <div className="rounded-2xl bg-gray-900 p-8 sm:p-10 text-center">
          <h3 className="text-xl font-bold text-white mb-2">Still have questions?</h3>
          <p className="text-sm text-gray-400 mb-6 max-w-md mx-auto">
            Our support team is available Monday to Saturday, 8am — 8pm GMT. We typically respond within 24 hours.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <a
              href="mailto:support@loadmovegh.com"
              className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-green-700 transition"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" />
              </svg>
              Email Support
            </a>
            <a
              href="tel:+233557542254"
              className="inline-flex items-center gap-2 rounded-lg bg-gray-800 px-6 py-2.5 text-sm font-semibold text-white ring-1 ring-gray-700 hover:bg-gray-700 transition"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z" />
              </svg>
              +233 557 542 254
            </a>
          </div>
        </div>
      </div>

      {/* Mini footer */}
      <footer className="border-t border-gray-200 bg-white py-6">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 text-center text-sm text-gray-500">
          &copy; {new Date().getFullYear()} LoadMoveGH Ltd. All rights reserved.
        </div>
      </footer>
    </main>
  );
}
