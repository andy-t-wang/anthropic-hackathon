# Anthropic-hackathon

LLM-powered automatic styling for white-label SAAS products.

https://github.com/andy-t-wang/anthropic-hackathon/assets/41224501/afbd3b4b-519d-4396-a354-a8b828e9e571

Youtube Link: https://youtu.be/vmj_HVbRTCY

## Inspiration
Homogeneous styling is often a deal breaker for many companies purchasing white-label products. Engineers end up spending a ton of time iterating on style requests from customers. As the customer base grows, ad-hoc styling for each implementation becomes extremely time-consuming and tedious. Using LLMs we are able to automate much of the work and generate style sheets by parsing the customer's webpage code. 

## What it does
Chameleon downloads the webpage source code from the URL, does some pre-processing to the input and then passes it into Claude 2 to generate the component theme.
We use PIL for helping reduce hallucinations.

## How we built it
Python, PIL, Claude, React, Stripe

## Challenges we ran into
Culling the DOM to fit the context 
Improving stability of the output and reducing hallucinations

## Accomplishments that we're proud of
Finishing a POC in 24 hours
## What we learned

100k context window enabled us to pass in the DOM
## What's next for Chameleon -- Automatically Style White-Label Software 
- Fonts
- Images
- Gradients
- Animations
- Able to create a comprehensive thematic library for each component.
- Continuous deploy (automatically detecting source code updates and regenerating the style sheet)
