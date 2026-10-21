/**
 * The keep-or-clear question.
 *
 * Three decisions worth defending:
 *
 *   1. It is asked once, and not on arrival. A question about data retention
 *      put to someone before they have written anything is friction attached to
 *      an abstraction. Asked after a couple of entries it is concrete: these
 *      entries, this decision.
 *   2. Not keeping is the default, and it holds while the question goes
 *      unanswered. Someone who ignores it, or who closes the page, has nothing
 *      written to the database at all. The default fails safe.
 *   3. Neither option is styled as the recommended one. A person on a shared
 *      or public computer should feel no pull toward keeping, and a person
 *      wanting to look back over a month should feel none toward clearing.
 */
export default function KeepChoice({ count, busy, onChoose, onDismiss }) {
  return (
    <div className="card keep-choice">
      <p className="keep-title">
        You have written {count} {count === 1 ? "entry" : "entries"}. Would you
        like them kept?
      </p>
      <p className="keep-body">
        Right now nothing you have written has been saved anywhere. It is held
        in this tab and goes when you close it. If you would like to look back
        over these entries another day, they can be kept on this computer
        instead. Either way there is still no name, no sign-in and no way to
        tell who wrote them, and you can delete them whenever you like.
      </p>
      <p className="keep-body keep-caution">
        If you are on a shared or public computer, choose to clear them.
      </p>

      <div className="keep-actions">
        <button
          className="quiet"
          disabled={busy}
          onClick={() => onChoose(false)}
        >
          Clear when I close the browser
        </button>
        <button
          className="quiet"
          disabled={busy}
          onClick={() => onChoose(true)}
        >
          Keep them on this computer
        </button>
      </div>

      <button className="linky keep-later" disabled={busy} onClick={onDismiss}>
        Not now, ask me later
      </button>
    </div>
  );
}
