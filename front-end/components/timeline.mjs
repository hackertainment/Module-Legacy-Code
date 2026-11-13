import {createBloom, handleRebloom} from "./bloom.mjs";

/**
 * Create a timeline component
 * @param {string} template - The ID of the template to clone
 * @param {Object} blooms - The timeline content, show whatever is passed and don't make decisions
 * @returns {DocumentFragment} - The timeline element
 */
function createTimeline(template, blooms) {
  if (!blooms) return;
  const timelineElement = document
    .getElementById(template)
    .content.cloneNode(true);

  // All the bits of the template we currently want to interact with
  const content = timelineElement.querySelector("[data-content]");
  const emptyMessage = timelineElement.querySelector("[data-empty]");

  // Show/hide appropriate messages
  const isEmpty = blooms.length === 0;
  emptyMessage.hidden = !isEmpty;

  const bloomsFragment = document.createDocumentFragment();
  // Accumulate blooms
  blooms.forEach((bloom) => {
    bloomsFragment.appendChild(createBloom("bloom-template", bloom));
  });

  // Add all blooms to the content container at once
  content.appendChild(bloomsFragment);

  // TODO: update heading maybe

  return timelineElement;
}

export {createTimeline};
