"""
邮件发送模块
用于发送监控任务的通知邮件
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from datetime import datetime
from typing import Dict, List
import json


class EmailSender:
    """邮件发送器"""
    
    def __init__(self, smtp_server: str = "smtp.qq.com", 
                 smtp_port: int = 465,
                 sender_email: str = "",
                 sender_password: str = ""):
        """
        初始化邮件发送器
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            sender_email: 发件人邮箱
            sender_password: 发件人密码（授权码）
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def send_monitor_alert(self, to_email: str, symbol: str, name: str,
                          conditions: List[Dict], market_data: Dict) -> bool:
        """
        发送监控预警邮件
        
        Args:
            to_email: 收件人邮箱
            symbol: 指数代码
            name: 指数名称
            conditions: 触发的条件列表
            market_data: 市场数据
            
        Returns:
            是否发送成功
        """
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr(("量化监控系统", self.sender_email))
            msg['To'] = to_email
            msg['Subject'] = Header(f"监控预警 - {name}({symbol})", 'utf-8')
            
            # 生成邮件内容
            html_content = self._generate_alert_html(symbol, name, conditions, market_data)
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送邮件
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            print(f"[EmailSender] 邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            print(f"[EmailSender] 邮件发送失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_alert_html(self, symbol: str, name: str, 
                            conditions: List[Dict], market_data: Dict) -> str:
        """
        生成预警邮件的HTML内容
        
        Args:
            symbol: 指数代码
            name: 指数名称
            conditions: 触发的条件列表
            market_data: 市场数据
            
        Returns:
            HTML内容
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 格式化条件列表
        conditions_html = ""
        for i, cond in enumerate(conditions, 1):
            cond_desc = cond.get('description', '未知条件')
            cond_value = cond.get('value', 'N/A')
            conditions_html += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">{i}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{cond_desc}</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #e74c3c;">{cond_value}</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, "Microsoft YaHei", sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .header h2 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px; }}
                .info-box {{ background: #f8f9fa; border-left: 4px solid #667eea; padding: 15px; margin: 20px 0; border-radius: 4px; }}
                .info-box h3 {{ margin: 0 0 10px 0; color: #333; font-size: 18px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #667eea; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 10px; border: 1px solid #ddd; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; border-top: 1px solid #eee; }}
                .alert-badge {{ background: #e74c3c; color: white; padding: 5px 10px; border-radius: 4px; font-size: 14px; display: inline-block; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📊 量化监控预警通知</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">监控条件已触发，请及时关注！</p>
                </div>
                
                <div class="content">
                    <div class="alert-badge">⚠️ 监控预警</div>
                    
                    <div class="info-box">
                        <h3>监控对象</h3>
                        <p style="margin: 5px 0;"><strong>代码：</strong>{symbol}</p>
                        <p style="margin: 5px 0;"><strong>名称：</strong>{name}</p>
                        <p style="margin: 5px 0;"><strong>时间：</strong>{current_time}</p>
                    </div>
                    
                    <h3 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">买入信号（满足任意条件）</h3>
                    <table>
                        <thead>
                            <tr>
                                <th width="10%">序号</th>
                                <th width="50%">条件</th>
                                <th width="40%">当前值</th>
                            </tr>
                        </thead>
                        <tbody>
                            {conditions_html}
                        </tbody>
                    </table>
                    
                    <div class="info-box">
                        <h3>市场数据</h3>
                        <table style="margin: 10px 0;">
                            <tr>
                                <td style="background: #f8f9fa; font-weight: bold;">收盘</td>
                                <td>{market_data.get('close', 'N/A')}</td>
                                <td style="background: #f8f9fa; font-weight: bold;">MA</td>
                                <td>{market_data.get('ma', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="background: #f8f9fa; font-weight: bold;">比例</td>
                                <td>{market_data.get('ratio', 'N/A')}</td>
                                <td style="background: #f8f9fa; font-weight: bold;">RSI14</td>
                                <td>{market_data.get('rsi14', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td style="background: #f8f9fa; font-weight: bold;">RSI30</td>
                                <td>{market_data.get('rsi30', 'N/A')}</td>
                                <td style="background: #f8f9fa; font-weight: bold;">时间</td>
                                <td>{market_data.get('date', 'N/A')}</td>
                            </tr>
                        </table>
                    </div>
                </div>
                
                <div class="footer">
                    <p>此邮件由量化决策系统自动发送，请勿回复</p>
                    <p style="margin-top: 10px;">© 2025 量化决策系统 | Powered by Python & Flask</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_test_email(self, to_email: str) -> bool:
        """
        发送测试邮件
        
        Args:
            to_email: 收件人邮箱
            
        Returns:
            是否发送成功
        """
        test_conditions = [
            {"description": "[CLOSE,0,c]-[MA,0,c,20])/[MA,0,c,20]<-8%", "value": "-8.5%"},
            {"description": "[RSI,0,c,14]<30", "value": "28.50"}
        ]
        
        test_market_data = {
            'close': '24503.85',
            'ma': '24075.09',
            'ratio': '1.78%',
            'rsi14': '63.99',
            'rsi30': '62.85',
            'date': '2025-09-26'
        }
        
        return self.send_monitor_alert(
            to_email, 
            "测试代码", 
            "测试指数",
            test_conditions,
            test_market_data
        )
