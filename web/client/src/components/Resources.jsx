import { HELPLINES, CAMPUS } from "../resources.js";

/**
 * People a person can actually reach.
 *
 * Two decisions worth defending:
 *
 *   1. It is shown at the moment a distress reading is returned, not filed away
 *      on an information page. Someone who has just read that their words
 *      suggest low mood should not have to go looking.
 *   2. It is styled like the rest of the interface and not as an alert. A red
 *      emergency panel tells a person they are in a crisis, which the system
 *      has no basis for saying and which would discourage the honesty the whole
 *      design depends on.
 *
 * Numbers are `tel:` links so that on a phone they can be dialled directly.
 */
export default function Resources({ compact = false }) {
  const entries = CAMPUS.name ? [...HELPLINES, CAMPUS] : HELPLINES;

  return (
    <div className={compact ? "resources compact" : "resources"}>
      <p className="resources-title">If you would like to talk to someone</p>
      <ul className="resources-list">
        {entries.map((item) => (
          <li key={item.name}>
            <span className="resource-name">{item.name}</span>
            {item.tel ? (
              <a className="resource-tel" href={`tel:${item.tel}`}>
                {item.display}
              </a>
            ) : null}
            <span className="resource-note">{item.note}</span>
          </li>
        ))}
      </ul>
      <p className="resources-foot">
        Calling is free on the toll-free lines. You do not have to be in a
        crisis to use them.
      </p>
    </div>
  );
}
