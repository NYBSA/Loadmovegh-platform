export default function PricingPage() {
  return (
    <main className="min-h-screen bg-gray-50">
      {/* ── Navbar ─────────────────────────────────────── */}
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
          <a href="/" className="btn-secondary text-sm px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition">
            &larr; Back to Home
          </a>
        </div>
      </nav>

      {/* ── Header ─────────────────────────────────────── */}
      <section className="py-16 text-center">
        <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
          Simple, Transparent Pricing
        </h1>
        <p className="mt-3 text-gray-500 max-w-xl mx-auto">
          No hidden fees. Pay only when freight moves. Platform commission is deducted automatically from each completed delivery.
        </p>
      </section>

      {/* ── Pricing Cards ──────────────────────────────── */}
      <section className="mx-auto max-w-5xl px-4 pb-20 grid gap-8 sm:grid-cols-3">
        {/* Free Tier */}
        <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm hover:shadow-md transition">
          <h3 className="text-lg font-bold text-gray-900">Starter</h3>
          <p className="mt-1 text-sm text-gray-500">For individual couriers &amp; small shippers</p>
          <div className="mt-6">
            <span className="text-4xl font-extrabold text-gray-900">Free</span>
            <span className="text-sm text-gray-500 ml-1">to join</span>
          </div>
          <p className="mt-1 text-sm text-green-600 font-medium">5% commission per delivery</p>
          <ul className="mt-8 space-y-3 text-sm text-gray-600">
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Access to load board
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Bid on loads
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Mobile Money wallet
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Escrow protection
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Basic AI price suggestions
            </li>
          </ul>
          <a href="/#auth" className="mt-8 block w-full text-center rounded-lg bg-gray-900 text-white py-2.5 text-sm font-semibold hover:bg-gray-800 transition">
            Get Started Free
          </a>
        </div>

        {/* Pro Tier */}
        <div className="rounded-2xl border-2 border-green-600 bg-white p-8 shadow-lg relative">
          <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-green-600 px-4 py-1 text-xs font-bold text-white">
            MOST POPULAR
          </span>
          <h3 className="text-lg font-bold text-gray-900">Professional</h3>
          <p className="mt-1 text-sm text-gray-500">For growing businesses &amp; fleets</p>
          <div className="mt-6">
            <span className="text-4xl font-extrabold text-gray-900">GHS 99</span>
            <span className="text-sm text-gray-500 ml-1">/month</span>
          </div>
          <p className="mt-1 text-sm text-green-600 font-medium">3.5% commission per delivery</p>
          <ul className="mt-8 space-y-3 text-sm text-gray-600">
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Everything in Starter
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              AI load matching
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Priority in search results
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Real-time GPS tracking
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              AI assistant (unlimited)
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Dedicated support
            </li>
          </ul>
          <a href="/#auth" className="mt-8 block w-full text-center rounded-lg bg-green-600 text-white py-2.5 text-sm font-semibold hover:bg-green-700 transition">
            Start Free Trial
          </a>
        </div>

        {/* Enterprise Tier */}
        <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm hover:shadow-md transition">
          <h3 className="text-lg font-bold text-gray-900">Enterprise</h3>
          <p className="mt-1 text-sm text-gray-500">For large logistics companies</p>
          <div className="mt-6">
            <span className="text-4xl font-extrabold text-gray-900">Custom</span>
          </div>
          <p className="mt-1 text-sm text-green-600 font-medium">Negotiated commission rate</p>
          <ul className="mt-8 space-y-3 text-sm text-gray-600">
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Everything in Professional
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              API access
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Custom integrations
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              Fleet management tools
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              White-label option
            </li>
            <li className="flex items-center gap-2">
              <svg className="h-4 w-4 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              SLA guarantee
            </li>
          </ul>
          <a href="mailto:hello@loadmovegh.com" className="mt-8 block w-full text-center rounded-lg bg-gray-900 text-white py-2.5 text-sm font-semibold hover:bg-gray-800 transition">
            Contact Sales
          </a>
        </div>
      </section>

      {/* ── FAQ ──────────────────────────────────────── */}
      <section className="mx-auto max-w-3xl px-4 pb-20">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-10">Frequently Asked Questions</h2>
        <div className="space-y-6">
          {[
            { q: "How does the commission work?", a: "A small percentage is deducted from each completed delivery payment. The shipper pays the full bid amount, and the courier receives the amount minus commission." },
            { q: "Is the escrow safe?", a: "Yes. Funds are held securely in escrow when a bid is accepted and only released to the courier after proof of delivery is confirmed." },
            { q: "Can I use Mobile Money?", a: "Absolutely! We support MTN Mobile Money for deposits, withdrawals, and all transactions on the platform." },
            { q: "What if there is a dispute?", a: "Our dispute resolution system allows both parties to submit evidence. An admin reviews the case and funds are released accordingly." },
          ].map((faq, i) => (
            <div key={i} className="rounded-xl bg-white border border-gray-200 p-6">
              <h4 className="font-semibold text-gray-900">{faq.q}</h4>
              <p className="mt-2 text-sm text-gray-500">{faq.a}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
