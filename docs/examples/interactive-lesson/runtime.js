function activate(sectionId) {
  document.querySelectorAll('[data-example-section]').forEach(section => { section.hidden = section.id !== sectionId; });
  document.querySelectorAll('[data-section]').forEach(button => button.classList.toggle('active', button.dataset.section === sectionId));
}
document.querySelectorAll('[data-section]').forEach(button => button.addEventListener('click', () => { activate(button.dataset.section); window.scrollTo(0, 0); }));
activate(document.querySelector('[data-example-section]').id);
document.addEventListener('click', event => {
  const button = event.target.closest('[data-ih-action]');
  if (!button) return;
  const block = button.closest('[data-block-id]');
  const id = button.dataset.interactionId;
  const feedback = block && Array.from(block.querySelectorAll('[data-ih-feedback-for]')).find(item => item.dataset.ihFeedbackFor === id);
  if (!feedback) return;
  feedback.classList.add('is-visible');
  feedback.style.display = 'block';
  if (button.dataset.ihAction === 'single-choice') {
    block.querySelectorAll('[data-option-id]').forEach(option => option.setAttribute('aria-pressed', String(option === button)));
    feedback.textContent = (button.dataset.correct === 'true' ? '回答正确。' : '再想一想。') + (button.dataset.feedback || '');
  }
  if (button.dataset.ihAction === 'short-answer-submit') {
    const input = Array.from(block.querySelectorAll('textarea')).find(item => item.dataset.ihInputFor === id);
    if (!input || input.value.trim().length < Number(button.dataset.minLength || 1)) {
      feedback.textContent = '请先填写回答，并达到题目要求的长度。';
      return;
    }
    feedback.textContent = '已在当前页面提交，可对照参考要点继续思考：' + (button.dataset.referencePoints || '回顾本节讲解。');
  }
});
