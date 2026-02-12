export default function PrivacyPolicyPage() {
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

      <article className="mx-auto max-w-3xl px-4 sm:px-6 py-12 sm:py-16">
        <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl mb-2">Privacy Policy</h1>
        <p className="text-sm text-gray-500 mb-10">Last updated: February 12, 2026</p>

        <div className="prose prose-gray max-w-none space-y-8 text-gray-700 text-[15px] leading-relaxed">

          {/* 1 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">1. Introduction</h2>
            <p>
              LoadMoveGH Ltd (&quot;LoadMoveGH,&quot; &quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) operates the freight marketplace platform at{" "}
              <a href="https://www.loadmovegh.com" className="text-green-600 hover:underline">www.loadmovegh.com</a> and related mobile applications.
              We are committed to protecting the privacy and security of our users (&quot;you&quot; or &quot;your&quot;) in accordance with the Ghana Data Protection Act, 2012 (Act 843).
            </p>
            <p className="mt-3">
              This Privacy Policy explains how we collect, use, store, share, and protect your personal information when you use our platform, whether as a shipper, courier, or visitor.
            </p>
          </section>

          {/* 2 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">2. Information We Collect</h2>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">2.1 Information You Provide</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li><strong>Account information:</strong> Full name, email address, phone number, password, role (shipper or courier).</li>
              <li><strong>Business information:</strong> Company name, business type, Ghana Post GPS address, TIN number (if applicable).</li>
              <li><strong>Vehicle information (couriers):</strong> Vehicle type, registration number, insurance details, licence information.</li>
              <li><strong>Payment information:</strong> Mobile Money number (MTN MoMo, Vodafone Cash, AirtelTigo Money), transaction history.</li>
              <li><strong>Identity verification:</strong> Ghana Card number, driver&apos;s licence, or passport for identity verification purposes.</li>
              <li><strong>Communications:</strong> Messages sent through our platform, support tickets, and feedback.</li>
            </ul>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">2.2 Information Collected Automatically</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li><strong>Device information:</strong> IP address, browser type, operating system, device identifiers.</li>
              <li><strong>Location data:</strong> GPS coordinates (with your consent) for load matching, route optimization, and delivery tracking.</li>
              <li><strong>Usage data:</strong> Pages visited, features used, search queries, bid history, click patterns.</li>
              <li><strong>Cookies and similar technologies:</strong> Session cookies, analytics cookies, and preference cookies.</li>
            </ul>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">2.3 Information from Third Parties</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>Mobile Money payment providers (MTN, Vodafone, AirtelTigo) — transaction confirmations.</li>
              <li>Identity verification services — for KYC compliance.</li>
              <li>Public business registries — for company verification.</li>
            </ul>
          </section>

          {/* 3 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">3. How We Use Your Information</h2>
            <p>We use your information for the following purposes:</p>
            <ul className="list-disc pl-5 space-y-1.5 mt-2">
              <li><strong>Platform operations:</strong> Creating and managing your account, facilitating load posting, bid submission, and delivery tracking.</li>
              <li><strong>Payment processing:</strong> Processing Mobile Money deposits, escrow payments, commission deductions, and withdrawals.</li>
              <li><strong>AI-powered services:</strong> Load matching, price recommendations, fraud detection, and route optimization.</li>
              <li><strong>Communications:</strong> Sending transaction notifications, delivery updates, bid alerts, and platform announcements.</li>
              <li><strong>Safety and security:</strong> Verifying identities, detecting fraud, preventing abuse, and resolving disputes.</li>
              <li><strong>Platform improvement:</strong> Analysing usage patterns, conducting research, and improving our services.</li>
              <li><strong>Legal compliance:</strong> Meeting regulatory obligations under Ghanaian law.</li>
            </ul>
          </section>

          {/* 4 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">4. Legal Basis for Processing</h2>
            <p>Under the Ghana Data Protection Act, 2012 (Act 843), we process your data based on:</p>
            <ul className="list-disc pl-5 space-y-1.5 mt-2">
              <li><strong>Consent:</strong> You consent to data processing when you create an account and accept these terms.</li>
              <li><strong>Contractual necessity:</strong> Processing is necessary to provide our freight marketplace services.</li>
              <li><strong>Legal obligation:</strong> We may process data to comply with Ghanaian tax, transport, and financial regulations.</li>
              <li><strong>Legitimate interest:</strong> For fraud prevention, platform security, and service improvement.</li>
            </ul>
          </section>

          {/* 5 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">5. Data Sharing</h2>
            <p>We may share your information with:</p>
            <ul className="list-disc pl-5 space-y-1.5 mt-2">
              <li><strong>Other platform users:</strong> Shippers see courier profiles (name, vehicle, rating) when receiving bids. Couriers see shipper company name and load details.</li>
              <li><strong>Payment providers:</strong> MTN MoMo, Vodafone Cash, and AirtelTigo Money for processing transactions.</li>
              <li><strong>Service providers:</strong> Cloud hosting (Vercel, Railway), database (Supabase), mapping (Google Maps), and analytics providers.</li>
              <li><strong>Law enforcement:</strong> When required by Ghanaian law, court order, or to protect safety.</li>
              <li><strong>Business transfers:</strong> In the event of a merger, acquisition, or sale of assets.</li>
            </ul>
            <p className="mt-3 font-medium">We never sell your personal data to third-party advertisers.</p>
          </section>

          {/* 6 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">6. Data Security</h2>
            <p>We implement industry-standard security measures to protect your data:</p>
            <ul className="list-disc pl-5 space-y-1.5 mt-2">
              <li>SSL/TLS encryption for all data in transit.</li>
              <li>Encrypted database storage for sensitive information.</li>
              <li>JWT-based authentication with token rotation.</li>
              <li>AI-powered fraud detection monitoring all transactions.</li>
              <li>Regular security audits and vulnerability assessments.</li>
              <li>Role-based access control for internal systems.</li>
            </ul>
          </section>

          {/* 7 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">7. Data Retention</h2>
            <ul className="list-disc pl-5 space-y-1.5">
              <li><strong>Active accounts:</strong> Data is retained for the duration of your account activity.</li>
              <li><strong>Closed accounts:</strong> Personal data is deleted within 90 days of account closure, except where retention is required by law.</li>
              <li><strong>Transaction records:</strong> Retained for 7 years as required by Ghana Revenue Authority (GRA) regulations.</li>
              <li><strong>Fraud prevention data:</strong> May be retained for up to 5 years to prevent repeat offenders.</li>
            </ul>
          </section>

          {/* 8 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">8. Your Rights</h2>
            <p>Under the Ghana Data Protection Act, you have the right to:</p>
            <ul className="list-disc pl-5 space-y-1.5 mt-2">
              <li><strong>Access:</strong> Request a copy of the personal data we hold about you.</li>
              <li><strong>Rectification:</strong> Request correction of inaccurate or incomplete data.</li>
              <li><strong>Erasure:</strong> Request deletion of your personal data (subject to legal retention requirements).</li>
              <li><strong>Restriction:</strong> Request limitation of processing in certain circumstances.</li>
              <li><strong>Portability:</strong> Request your data in a structured, machine-readable format.</li>
              <li><strong>Objection:</strong> Object to processing based on legitimate interest.</li>
              <li><strong>Withdraw consent:</strong> Withdraw consent at any time (without affecting prior processing).</li>
            </ul>
            <p className="mt-3">
              To exercise any of these rights, email us at{" "}
              <a href="mailto:privacy@loadmovegh.com" className="text-green-600 hover:underline">privacy@loadmovegh.com</a>.
              We will respond within 30 days.
            </p>
          </section>

          {/* 9 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">9. Cookies</h2>
            <p>We use the following types of cookies:</p>
            <ul className="list-disc pl-5 space-y-1.5 mt-2">
              <li><strong>Essential cookies:</strong> Required for login, security, and basic platform functionality.</li>
              <li><strong>Analytics cookies:</strong> Help us understand how users interact with the platform.</li>
              <li><strong>Preference cookies:</strong> Remember your settings and preferences.</li>
            </ul>
            <p className="mt-3">You can manage cookie preferences through your browser settings.</p>
          </section>

          {/* 10 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">10. Children&apos;s Privacy</h2>
            <p>
              LoadMoveGH is not intended for users under the age of 18. We do not knowingly collect personal data from children.
              If you believe a child has provided us with personal data, please contact us immediately.
            </p>
          </section>

          {/* 11 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">11. International Data Transfers</h2>
            <p>
              Your data may be processed on servers located outside Ghana (including the United States and Europe) by our
              hosting and service providers. We ensure appropriate safeguards are in place, including contractual obligations
              that provide equivalent data protection to the Ghana Data Protection Act.
            </p>
          </section>

          {/* 12 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">12. Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. We will notify you of significant changes via email or
              a prominent notice on our platform. Your continued use of LoadMoveGH after changes constitutes acceptance of the updated policy.
            </p>
          </section>

          {/* 13 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">13. Contact Us</h2>
            <p>For privacy-related questions or to exercise your data rights, contact us:</p>
            <div className="mt-3 rounded-xl bg-white border border-gray-200 p-5 space-y-2 text-sm">
              <p><strong>LoadMoveGH Ltd — Data Protection Office</strong></p>
              <p>Email: <a href="mailto:privacy@loadmovegh.com" className="text-green-600 hover:underline">privacy@loadmovegh.com</a></p>
              <p>Phone: <a href="tel:+233557542254" className="text-green-600 hover:underline">+233 557 542 254</a></p>
              <p>Website: <a href="https://www.loadmovegh.com" className="text-green-600 hover:underline">www.loadmovegh.com</a></p>
            </div>
            <p className="mt-4 text-sm text-gray-500">
              You may also lodge a complaint with the <strong>Data Protection Commission of Ghana</strong> at{" "}
              <a href="https://www.dataprotection.org.gh" target="_blank" rel="noopener noreferrer" className="text-green-600 hover:underline">www.dataprotection.org.gh</a>.
            </p>
          </section>

        </div>
      </article>

      {/* Mini footer */}
      <footer className="border-t border-gray-200 bg-white py-6">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 text-center text-sm text-gray-500">
          &copy; {new Date().getFullYear()} LoadMoveGH Ltd. All rights reserved.
        </div>
      </footer>
    </main>
  );
}
