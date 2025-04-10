import { Document, Packer, Paragraph, HeadingLevel, TextRun } from 'docx';
import { saveAs } from 'file-saver';

// 清理Markdown中的多余标题标记
export function cleanMarkdown(text: string): string {
  // 清除内容开头的多余标题标记
  let cleanText = text.replace(/^###\s+[^\n]*\n?/, '');
  // 清除内容中所有的三级及以上标题标记（保留其文本内容）
  cleanText = cleanText.replace(/^#{3,}\s+([^\n]*)\n?/gm, '$1\n');
  return cleanText;
}

// 简化版的Markdown解析函数 - 只处理最常见的格式
export function parseMarkdownForWord(markdownText: string): Paragraph[] {
  const paragraphs: Paragraph[] = [];
  
  // 按行分割
  const lines = markdownText.split('\n');
  
  for (const line of lines) {
    const trimmedLine = line.trim();
    if (trimmedLine === '') continue; // 跳过空行
    
    // 检测标题
    const headingMatch = trimmedLine.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const headingText = headingMatch[2];
      
      let headingLevel;
      if (level === 1) headingLevel = HeadingLevel.HEADING_1;
      else if (level === 2) headingLevel = HeadingLevel.HEADING_2;
      else headingLevel = HeadingLevel.HEADING_3;
      
      paragraphs.push(
        new Paragraph({
          text: headingText,
          heading: headingLevel,
          spacing: {
            before: 200,
            after: 120,
          }
        })
      );
      continue;
    }
    
    // 处理普通段落，解析粗体格式
    const textRuns: TextRun[] = [];
    let remainingText = trimmedLine;
    
    // 处理粗体
    let boldMatch;
    const boldRegex = /\*\*([^*]+)\*\*/g;
    let lastIndex = 0;
    
    while ((boldMatch = boldRegex.exec(remainingText)) !== null) {
      // 添加粗体前的普通文本
      if (boldMatch.index > lastIndex) {
        textRuns.push(
          new TextRun({
            text: remainingText.substring(lastIndex, boldMatch.index),
            size: 24,
          })
        );
      }
      
      // 添加粗体文本
      textRuns.push(
        new TextRun({
          text: boldMatch[1],
          bold: true,
          size: 24,
        })
      );
      
      lastIndex = boldMatch.index + boldMatch[0].length;
    }
    
    // 添加剩余的文本
    if (lastIndex < remainingText.length) {
      textRuns.push(
        new TextRun({
          text: remainingText.substring(lastIndex),
          size: 24,
        })
      );
    }
    
    // 如果没有特殊格式，则添加整段文本
    if (textRuns.length === 0) {
      textRuns.push(
        new TextRun({
          text: trimmedLine,
          size: 24,
        })
      );
    }
    
    paragraphs.push(
      new Paragraph({
        children: textRuns,
        spacing: {
          after: 200,
        }
      })
    );
  }
  
  return paragraphs;
}

// 生成并下载Word文档
export function generateWordDocument(
  mainTitle: string, 
  chapters: { title: string; content: string }[]
): Promise<void> {
  const doc = new Document({
    sections: [
      {
        properties: {},
        children: [
          new Paragraph({
            text: mainTitle,
            heading: HeadingLevel.HEADING_1,
          }),
          ...chapters.flatMap((chapter) => {
            const chapterElements = [
              new Paragraph({
                text: chapter.title,
                heading: HeadingLevel.HEADING_2,
                spacing: {
                  before: 400,
                  after: 200,
                },
              })
            ];
            
            // 清理内容并解析Markdown格式
            const cleanContent = cleanMarkdown(chapter.content);
            const contentElements = parseMarkdownForWord(cleanContent);
            
            return [...chapterElements, ...contentElements];
          }),
        ],
      },
    ],
  });

  // 生成Word文档并下载
  return Packer.toBlob(doc).then(blob => {
    saveAs(blob, `${mainTitle || '论文写作助手生成内容'}.docx`);
    return Promise.resolve();
  });
}

// 生成并下载Markdown文档
export function generateMarkdownDocument(
  mainTitle: string, 
  chapters: { title: string; content: string }[]
): void {
  let markdownText = `# ${mainTitle}\n\n`;
  
  chapters.forEach((chapter) => {
    markdownText += `## ${chapter.title}\n\n`;
    
    // 清理章节内容中的多余标题标记
    const cleanContent = cleanMarkdown(chapter.content);
    markdownText += `${cleanContent}\n\n`;
  });
  
  const blob = new Blob([markdownText], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${mainTitle}.md`;
  a.click();
  URL.revokeObjectURL(url);
}