import React, { useState, useEffect } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { Elements } from "@stripe/react-stripe-js";

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
  useEffect(() => {
    // Create PaymentIntent as soon as the page loads
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
      colorPrimary: "#191919",
      colorBackground: "#FFFFFF",
      colorText: "#191919",
      colorDanger: "#BF4D43",
    },
  };
  const options = {
    clientSecret,
    appearance,
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    console.log(url);
    console.log("here");
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
        <button type="submit">Submit</button>
      </form>
      {clientSecret && (
        <Elements options={options} stripe={stripePromise}>
          <CheckoutForm />
        </Elements>
      )}
    </div>
  );
}
