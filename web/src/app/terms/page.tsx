export default function TermsOfUsePage() {
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
        <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl mb-2">Terms of Use</h1>
        <p className="text-sm text-gray-500 mb-10">Last updated: February 12, 2026</p>

        <div className="prose prose-gray max-w-none space-y-8 text-gray-700 text-[15px] leading-relaxed">

          {/* 1 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">1. Acceptance of Terms</h2>
            <p>
              By accessing or using the LoadMoveGH platform at{" "}
              <a href="https://www.loadmovegh.com" className="text-green-600 hover:underline">www.loadmovegh.com</a>,
              our mobile applications, or any related services (collectively, the &quot;Platform&quot;), you agree to be bound by these Terms of Use
              (&quot;Terms&quot;). If you do not agree to these Terms, do not use the Platform.
            </p>
            <p className="mt-3">
              LoadMoveGH Ltd (&quot;LoadMoveGH,&quot; &quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) is a company registered in Ghana
              that operates a freight marketplace connecting shippers with courier drivers.
            </p>
          </section>

          {/* 2 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">2. Eligibility</h2>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>You must be at least 18 years old to use the Platform.</li>
              <li>If registering as a business, you must have the authority to bind that business to these Terms.</li>
              <li>Courier drivers must hold a valid Ghana driver&apos;s licence appropriate for their vehicle type.</li>
              <li>All users must provide accurate, complete, and current registration information.</li>
              <li>You are responsible for maintaining the confidentiality of your account credentials.</li>
            </ul>
          </section>

          {/* 3 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">3. Platform Services</h2>
            <p>LoadMoveGH provides a marketplace platform that enables:</p>
            <ul className="list-disc pl-5 space-y-1.5 mt-2">
              <li><strong>Shippers:</strong> To post freight loads, receive and compare bids, accept bids, make escrow payments, and track deliveries.</li>
              <li><strong>Couriers:</strong> To browse available loads, submit bids, accept jobs, receive payments, and manage their earnings.</li>
            </ul>
            <p className="mt-3 font-medium">
              LoadMoveGH acts solely as an intermediary marketplace. We are not a transport company, carrier, or freight forwarder.
              The contract for carriage is between the shipper and the courier directly.
            </p>
          </section>

          {/* 4 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">4. User Accounts &amp; Roles</h2>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">4.1 Shipper Accounts</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>Must provide valid company name and business details.</li>
              <li>Are responsible for accurately describing loads (weight, dimensions, pickup/delivery locations, special requirements).</li>
              <li>Must fund escrow before a courier can begin a delivery.</li>
              <li>Must confirm proof of delivery to release escrow funds.</li>
            </ul>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">4.2 Courier Accounts</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>Must provide valid vehicle information, driver&apos;s licence, and insurance details.</li>
              <li>Are solely responsible for the safe and timely transport of goods.</li>
              <li>Must maintain appropriate vehicle insurance and road-worthiness certificates.</li>
              <li>Must comply with all applicable Ghanaian transport regulations (DVLA, NRSA).</li>
            </ul>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">4.3 Account Security</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>You are responsible for all activity under your account.</li>
              <li>Notify us immediately at <a href="mailto:support@loadmovegh.com" className="text-green-600 hover:underline">support@loadmovegh.com</a> if you suspect unauthorized access.</li>
              <li>Do not share your account credentials or allow others to use your account.</li>
            </ul>
          </section>

          {/* 5 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">5. Payments, Escrow &amp; Fees</h2>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">5.1 Escrow System</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>When a shipper accepts a bid, the agreed amount is held in escrow via our secure payment system.</li>
              <li>Funds are released to the courier only after the shipper confirms successful delivery (proof of delivery).</li>
              <li>If a dispute arises, funds remain in escrow until the dispute is resolved.</li>
            </ul>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">5.2 Platform Commission</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>LoadMoveGH charges a commission on each completed delivery, deducted automatically from the payment.</li>
              <li>Current commission rates are displayed on our <a href="/pricing" className="text-green-600 hover:underline">Pricing page</a>.</li>
              <li>Commission rates may be updated with 30 days&apos; prior notice.</li>
            </ul>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">5.3 Mobile Money</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>All payments are processed through MTN Mobile Money, Vodafone Cash, or AirtelTigo Money.</li>
              <li>Mobile Money provider fees may apply to deposits and withdrawals.</li>
              <li>LoadMoveGH is not responsible for delays or failures caused by Mobile Money providers.</li>
            </ul>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">5.4 Wallet</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>Each user has a LoadMoveGH wallet for platform transactions.</li>
              <li>Wallet balances are not interest-bearing and do not constitute bank deposits.</li>
              <li>Minimum withdrawal amount: GHS 5.00. Maximum single transaction: GHS 50,000.</li>
            </ul>
          </section>

          {/* 6 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">6. Bidding &amp; Jobs</h2>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>Bids submitted by couriers are binding offers to transport the described load at the stated price.</li>
              <li>Shippers are free to accept, reject, or negotiate any bid.</li>
              <li>Once a bid is accepted and escrow is funded, both parties are committed to the job.</li>
              <li>Cancellation by the shipper after escrow funding may result in a cancellation fee.</li>
              <li>Repeated cancellations or no-shows by either party may result in account suspension.</li>
              <li>LoadMoveGH&apos;s AI pricing suggestions are recommendations only and do not constitute a price guarantee.</li>
            </ul>
          </section>

          {/* 7 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">7. Prohibited Conduct</h2>
            <p>You agree not to:</p>
            <ul className="list-disc pl-5 space-y-1.5 mt-2">
              <li>Post fraudulent loads or submit fraudulent bids.</li>
              <li>Transport illegal, hazardous, or prohibited goods without proper permits and disclosure.</li>
              <li>Manipulate bids, ratings, or reviews.</li>
              <li>Create multiple accounts to circumvent restrictions or bans.</li>
              <li>Attempt to bypass the platform to avoid commission (off-platform transactions).</li>
              <li>Use the platform to harass, threaten, or abuse other users.</li>
              <li>Interfere with the platform&apos;s security, infrastructure, or other users&apos; access.</li>
              <li>Scrape, crawl, or use automated tools to extract data from the platform.</li>
              <li>Misrepresent your identity, qualifications, vehicle type, or business status.</li>
            </ul>
          </section>

          {/* 8 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">8. Dispute Resolution</h2>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>Disputes between shippers and couriers should first be raised through the platform&apos;s dispute system.</li>
              <li>Both parties may submit evidence (photos, GPS data, communications) for review.</li>
              <li>LoadMoveGH will review disputes and make a determination within 7 business days.</li>
              <li>Escrow funds in dispute are held until resolution.</li>
              <li>LoadMoveGH&apos;s dispute determination is final for platform-related matters.</li>
              <li>Nothing in these Terms prevents either party from seeking resolution through Ghanaian courts or the Alternative Dispute Resolution (ADR) Act, 2010 (Act 798).</li>
            </ul>
          </section>

          {/* 9 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">9. Liability &amp; Insurance</h2>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">9.1 Limitation of Liability</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>LoadMoveGH is a marketplace platform and does not provide transport services directly.</li>
              <li>We are not liable for damage, loss, theft, or delay of goods during transport.</li>
              <li>We are not liable for the actions, omissions, or representations of any user.</li>
              <li>Our total liability to you shall not exceed the fees paid to LoadMoveGH in the 12 months preceding the claim.</li>
            </ul>

            <h3 className="text-base font-semibold text-gray-900 mt-4 mb-2">9.2 Insurance</h3>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>Couriers are responsible for maintaining adequate goods-in-transit insurance.</li>
              <li>Shippers are encouraged to insure high-value goods independently.</li>
              <li>LoadMoveGH does not provide cargo insurance coverage.</li>
            </ul>
          </section>

          {/* 10 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">10. Intellectual Property</h2>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>The LoadMoveGH name, logo, and platform design are the property of LoadMoveGH Ltd.</li>
              <li>Content you post (load descriptions, reviews) remains yours, but you grant us a licence to display it on the platform.</li>
              <li>You may not copy, modify, or distribute any part of the platform without our written consent.</li>
            </ul>
          </section>

          {/* 11 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">11. Account Suspension &amp; Termination</h2>
            <p>We may suspend or terminate your account if you:</p>
            <ul className="list-disc pl-5 space-y-1.5 mt-2">
              <li>Breach these Terms of Use.</li>
              <li>Engage in fraudulent activity or prohibited conduct.</li>
              <li>Receive consistently poor ratings or multiple verified complaints.</li>
              <li>Fail to resolve disputes or respond to platform communications.</li>
              <li>Are flagged by our AI fraud detection system.</li>
            </ul>
            <p className="mt-3">
              You may close your account at any time by contacting{" "}
              <a href="mailto:support@loadmovegh.com" className="text-green-600 hover:underline">support@loadmovegh.com</a>.
              Outstanding escrow obligations must be settled before account closure.
            </p>
          </section>

          {/* 12 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">12. Indemnification</h2>
            <p>
              You agree to indemnify and hold harmless LoadMoveGH Ltd, its directors, employees, and agents from any claims,
              losses, damages, liabilities, and expenses (including legal fees) arising from your use of the Platform,
              your violation of these Terms, or your violation of any rights of a third party.
            </p>
          </section>

          {/* 13 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">13. Disclaimer of Warranties</h2>
            <p>
              The Platform is provided on an &quot;as is&quot; and &quot;as available&quot; basis. LoadMoveGH makes no warranties,
              express or implied, regarding the Platform&apos;s reliability, availability, accuracy, or fitness for a particular purpose.
              We do not guarantee that:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 mt-2">
              <li>The Platform will be uninterrupted or error-free.</li>
              <li>AI-powered price suggestions will be accurate in all market conditions.</li>
              <li>All users on the Platform are verified and trustworthy.</li>
              <li>Any specific load or courier match will result in a successful delivery.</li>
            </ul>
          </section>

          {/* 14 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">14. Governing Law</h2>
            <p>
              These Terms shall be governed by and construed in accordance with the laws of the Republic of Ghana.
              Any dispute arising under these Terms shall be subject to the exclusive jurisdiction of the courts of Ghana,
              unless resolved through alternative dispute resolution.
            </p>
          </section>

          {/* 15 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">15. Changes to These Terms</h2>
            <p>
              We reserve the right to modify these Terms at any time. We will notify users of material changes via email
              or a prominent platform notice at least 14 days before the changes take effect. Continued use of the Platform
              after changes constitutes acceptance of the updated Terms.
            </p>
          </section>

          {/* 16 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">16. Severability</h2>
            <p>
              If any provision of these Terms is found to be unenforceable or invalid by a court of competent jurisdiction,
              the remaining provisions shall continue in full force and effect.
            </p>
          </section>

          {/* 17 */}
          <section>
            <h2 className="text-xl font-bold text-gray-900 mb-3">17. Contact Us</h2>
            <p>For questions about these Terms of Use, contact us:</p>
            <div className="mt-3 rounded-xl bg-white border border-gray-200 p-5 space-y-2 text-sm">
              <p><strong>LoadMoveGH Ltd — Legal Department</strong></p>
              <p>Email: <a href="mailto:legal@loadmovegh.com" className="text-green-600 hover:underline">legal@loadmovegh.com</a></p>
              <p>Phone: <a href="tel:+233557542254" className="text-green-600 hover:underline">+233 557 542 254</a></p>
              <p>Website: <a href="https://www.loadmovegh.com" className="text-green-600 hover:underline">www.loadmovegh.com</a></p>
            </div>
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
