import { useEffect, useState } from "react";

import Resources from "./Resources.jsx";

/**
 * What the system is, and what it is not.
 *
 * Stating the limits plainly is not a disclaimer exercise. Someone deciding
 * whether to be honest with a machine is entitled to know what it does with
 * their words and how much weight to put on its answer.
 *
 * The contacts are repeated here as well as on a result, so that a person who
 * came looking for them, rather than being shown them, can still find them.
 */
export default function About() {
  const [info, setInfo] = useState(null);

  useEffect(() => {
    fetch("/api/info")
      .then((response) => response.json())
      .then((payload) => setInfo(payload.ok ? payload : null))
      .catch(() => setInfo(null));
  }, []);

  return (
    <div className="card about">
      <h3>What this does</h3>
      <p>
        It reads what you write and says which of four patterns your words most
        resemble: no clear distress, low mood, worry, or pressure. It reports a
        pattern in language. It does not examine you, and it cannot know you.
      </p>

      <h3>What it is not</h3>
      <p>
        It is not a diagnosis, and it is not a substitute for talking to
        someone. A machine that counts words cannot tell the difference between
        a hard week and a serious illness. If something it says worries you, or
        if it says nothing is wrong and you know otherwise, trust yourself over
        it and speak to someone you trust or a health professional.
      </p>

      <Resources />

      <h3>What happens to what you write</h3>
      <p>
        There is no account and no sign-in. You are never asked for your name,
        your number or your email, and nothing is sent anywhere else.
      </p>
      <p>
        By default nothing is saved at all. What you write is held in this
        browser tab and goes when you close it. It is never written to the
        system&apos;s records. After a couple of entries you are asked once
        whether you would like them kept on this computer instead, so that you
        can look back at them another day. You can change that answer at any
        time from the entries page, in either direction, and deleting an entry
        deletes it.
      </p>

      <h3>Where it is weakest</h3>
      <p>
        It reads emotional words. If you describe a situation without saying how
        it felt, it will often read that as no distress. It was trained on
        English text written outside Nigeria, so Pidgin and heavily
        code-switched writing are less reliable. It is weakest at telling
        pressure apart from low mood. When it is unsure, it says so rather than
        guessing.
      </p>

      {info?.model && (
        <>
          <h3>The model behind it</h3>
          <dl>
            <dt>Classifier</dt>
            <dd>{info.model.name}</dd>
            <dt>Categories</dt>
            <dd>{info.model.classes.join(", ")}</dd>
            <dt>Trained on</dt>
            <dd>{info.model.train_records?.toLocaleString()} examples</dd>
            <dt>Tested on</dt>
            <dd>{info.model.test_records?.toLocaleString()} unseen examples</dd>
            {info.model.test_f1_weighted && (
              <>
                <dt>F1 score</dt>
                <dd>{info.model.test_f1_weighted}</dd>
              </>
            )}
            <dt>Last trained</dt>
            <dd>{info.model.trained_at}</dd>
          </dl>
        </>
      )}
    </div>
  );
}
