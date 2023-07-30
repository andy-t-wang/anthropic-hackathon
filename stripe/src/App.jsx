import React, { useState, useEffect } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { Elements } from "@stripe/react-stripe-js";
import ClipLoader from "react-spinners/ClipLoader";

import CheckoutForm from "./CheckoutForm";
import "./App.css";

// Make sure to call loadStripe outside of a component’s render to avoid
// recreating the Stripe object on every render.
// This is a public sample test API key.
// Don’t submit any personally identifiable information in requests made with this key.
// Sign in to see your own test API key embedded in code samples.
const stripePromise = loadStripe("pk_test_TYooMQauvdEDq54NiTphI7jx");

export default function App() {
  const [clientSecret, setClientSecret] = useState("");
  const [url, setUrl] = useState("");
  let [loading, setLoading] = useState(false);

  const [textcolor, setBodyFontColor] = useState("#000000");
  useEffect(() => {
    // Create PaymentIntent as soon as the page loads
    const getBodyFontColor = () => {
      const styles = window.getComputedStyle(document.forms[0]);
      const fontColor = styles.getPropertyValue("color");
      setBodyFontColor(fontColor);
    };

    getBodyFontColor();
    fetch("/create-payment-intent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: [{ id: "xl-tshirt" }] }),
    })
      .then((res) => res.json())
      .then((data) => setClientSecret(data.clientSecret));
  }, []);

  const appearance = {
    theme: "stripe",
    variables: {
      fontFamily: "Styrene B LC, sans-serif",
      fontSizeBase: "16px",
      colorPrimary: "#fff",
    },
    rules: {
      ".Label": {
        color: textcolor,
      },
    },
  };
  const options = {
    clientSecret,
    appearance,
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    console.log("1");
    await getCSSFile();
  };

  const getCSSFile = async () => {
    setLoading(true);
    const response = await fetch("http://127.0.0.1:5000/post_endpoint", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: url }),
    });
    const data = await response.json();
    setLoading(false);
  };

  return (
    <div className="App">
      <h1>Checkout</h1>
      <form onSubmit={handleSubmit}>
        <input
          className="textInput"
          type="text"
          onChange={(e) => setUrl(e.currentTarget.value)}
        />
        <button type="submit" onSubmit={handleSubmit}>
          Submit
        </button>
      </form>

      {clientSecret && (
        <Elements options={options} stripe={stripePromise}>
          <CheckoutForm />
        </Elements>
      )}
      <div
        style={{
          width: "100%",
          alignItems: "center",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <ClipLoader
          color={"black"}
          loading={loading}
          size={50}
          aria-label="Loading Spinner"
          data-testid="loader"
        />
      </div>
    </div>
  );
}
