import Confidence from "./Confidence.jsx";
import Resources from "./Resources.jsx";
import { CLASS_COLOURS } from "../classes.js";

/**
 * The result view.
 *
 * Four things are deliberate here and are worth defending:
 *
 *   1. When the model is not confident, the interface says so instead of
 *      naming a category. A screening aid that presents a 47% guess with the
 *      same certainty as a 97% reading is misleading its user.
 *   2. Nothing is phrased as a diagnosis. The wording is always about what the
 *      words resemble.
 *   3. The referral prompt is an invitation, not an alarm. It uses the same
 *      calm colour as the rest of the interface, because someone who has just
 *      been told their writing suggests distress does not need a red banner.
 *   4. The referral names people who can actually be reached. Advising someone
 *      to speak to a professional and then naming nobody leaves the work of
 *      finding one to the person least placed to do it. The contacts follow the
 *      referral note directly, and appear in a quieter form when the reading is
 *      inconclusive, because an unclear result is not a reason to withhold
 *      them.
 */
export default function Result({ result }) {
  if (!result) return null;

  const {
    predictedClass, confidence, probabilities, headline, message,
    refer, referralNote, uncertain,
  } = result;

  return (
    <div className="result card">
      <div className="result-head">
        <span className="chip">
          <span
            className="dot"
            style={{ background: CLASS_COLOURS[predictedClass] }}
          />
          {uncertain ? "No clear reading" : predictedClass}
        </span>
        <span className="entry-when">
          {(confidence * 100).toFixed(0)}% confidence
        </span>
      </div>

      {uncertain ? (
        <>
          <h2>Your words don&apos;t point clearly in any one direction</h2>
          <p>
            The strongest reading was <strong>{predictedClass}</strong>, but not
            by enough for the system to stand behind it. That often just means
            the entry is short, or mixes several things together. It is not a
            sign that anything is wrong, and it is not a sign that nothing is.
          </p>
          <p>
            If you would like a clearer reading, try writing a little more about
            how you have been feeling in your own words, in whatever way comes
            naturally.
          </p>
        </>
      ) : (
        <>
          <h2>{headline}</h2>
          <p>{message}</p>
        </>
      )}

      {refer && !uncertain && referralNote && (
        <div className="referral">{referralNote}</div>
      )}

      {/* A Normal reading is the one case where the system has nothing to
          hand back. Rather than closing on a flat "nothing detected", it
          offers something small and harmless. The wording is careful not to
          instruct and not to imply that anything needs fixing. */}
      {!refer && !uncertain && predictedClass === "Normal" && (
        <div className="suggestion">
          Nothing here suggests you need to do anything. Still, if you can, take
          a walk ten or fifteen minutes outside, without your phone. It is a
          small thing, and it tends to be worth it either way.
        </div>
      )}

      {refer && !uncertain && <Resources />}
      {uncertain && <Resources compact />}

      <Confidence probabilities={probabilities} />
    </div>
  );
}
