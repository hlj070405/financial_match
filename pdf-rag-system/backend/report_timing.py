"""
财报披露时间规则和智能报告类型选择
根据当前时间和披露规则，自动选择最合适的报告类型
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from enum import Enum

class ReportType(Enum):
    """报告类型"""
    ANNUAL = "annual"      # 年报
    SEMI_ANNUAL = "semi"   # 中报（半年报）
    Q1 = "q1"             # 一季报
    Q3 = "q3"             # 三季报

class ReportTimingService:
    """财报时间规则服务"""
    
    # 披露时间规则（最晚披露时间）
    DISCLOSURE_RULES = {
        ReportType.ANNUAL: {"month": 4, "day": 30},      # 年报：次年4月30日前
        ReportType.Q1: {"month": 4, "day": 30},          # 一季报：4月30日前
        ReportType.SEMI_ANNUAL: {"month": 8, "day": 31}, # 中报：8月31日前
        ReportType.Q3: {"month": 10, "day": 31},         # 三季报：10月31日前
    }
    
    # 巨潮资讯网的category参数
    CATEGORY_MAP = {
        ReportType.ANNUAL: "category_ndbg_szsh",      # 年度报告
        ReportType.SEMI_ANNUAL: "category_bndbg_szsh", # 半年度报告
        ReportType.Q1: "category_yjdbg_szsh",         # 第一季度报告
        ReportType.Q3: "category_sjdbg_szsh",         # 第三季度报告
    }
    
    # 报告类型的中文名称
    REPORT_NAME_MAP = {
        ReportType.ANNUAL: "年度报告",
        ReportType.SEMI_ANNUAL: "半年度报告",
        ReportType.Q1: "第一季度报告",
        ReportType.Q3: "第三季度报告",
    }
    
    @staticmethod
    def get_available_reports(target_date: Optional[datetime] = None) -> List[Dict]:
        """
        获取当前时间点可用的报告类型列表（按时效性排序）
        
        Args:
            target_date: 目标日期，默认为当前时间
            
        Returns:
            可用报告列表，格式：[{"type": ReportType, "year": int, "quarter": str, "priority": int}]
            priority越小越优先
        """
        if target_date is None:
            target_date = datetime.now()
        
        current_year = target_date.year
        current_month = target_date.month
        current_day = target_date.day
        
        available = []
        
        # 检查2025年三季报（10月31日前披露）
        if current_month >= 11 or (current_month == 10 and current_day >= 31):
            available.append({
                "type": ReportType.Q3,
                "year": current_year,
                "quarter": "Q3",
                "period": f"{current_year}Q3",
                "priority": 1,
                "description": f"{current_year}年三季报"
            })
        
        # 检查2025年中报（8月31日前披露）
        if current_month >= 9 or (current_month == 8 and current_day >= 31):
            available.append({
                "type": ReportType.SEMI_ANNUAL,
                "year": current_year,
                "quarter": "H1",
                "period": f"{current_year}H1",
                "priority": 2,
                "description": f"{current_year}年中报"
            })
        
        # 检查2025年一季报（4月30日前披露）
        if current_month >= 5 or (current_month == 4 and current_day >= 30):
            available.append({
                "type": ReportType.Q1,
                "year": current_year,
                "quarter": "Q1",
                "period": f"{current_year}Q1",
                "priority": 3,
                "description": f"{current_year}年一季报"
            })
        
        # 检查2024年年报（2025年4月30日前披露）
        if current_month >= 5 or (current_month == 4 and current_day >= 30):
            available.append({
                "type": ReportType.ANNUAL,
                "year": current_year - 1,
                "quarter": "FY",
                "period": f"{current_year - 1}",
                "priority": 4,
                "description": f"{current_year - 1}年年报"
            })
        
        # 如果当前在1-4月，2024年报可能还未披露，添加2023年报作为备选
        if current_month <= 4:
            available.append({
                "type": ReportType.ANNUAL,
                "year": current_year - 2,
                "quarter": "FY",
                "period": f"{current_year - 2}",
                "priority": 5,
                "description": f"{current_year - 2}年年报"
            })
        
        # 添加上一年的季报作为备选
        if current_month <= 4:
            available.append({
                "type": ReportType.Q3,
                "year": current_year - 1,
                "quarter": "Q3",
                "period": f"{current_year - 1}Q3",
                "priority": 6,
                "description": f"{current_year - 1}年三季报"
            })
        
        # 按优先级排序
        available.sort(key=lambda x: x["priority"])
        
        return available
    
    @staticmethod
    def get_best_report_type(user_year: Optional[int] = None, 
                            user_quarter: Optional[str] = None,
                            target_date: Optional[datetime] = None) -> Dict:
        """
        根据用户需求和当前时间，选择最合适的报告类型
        
        Args:
            user_year: 用户指定的年份
            user_quarter: 用户指定的季度（Q1/Q2/Q3/Q4/H1）
            target_date: 目标日期
            
        Returns:
            最佳报告信息
        """
        available = ReportTimingService.get_available_reports(target_date)
        
        if not available:
            # 降级：返回去年年报
            current_year = (target_date or datetime.now()).year
            return {
                "type": ReportType.ANNUAL,
                "year": current_year - 1,
                "quarter": "FY",
                "period": f"{current_year - 1}",
                "priority": 99,
                "description": f"{current_year - 1}年年报（降级）"
            }
        
        # 如果用户指定了年份和季度
        if user_year and user_quarter:
            quarter_map = {
                "Q1": ReportType.Q1,
                "Q2": ReportType.SEMI_ANNUAL,  # Q2用中报代替
                "H1": ReportType.SEMI_ANNUAL,
                "Q3": ReportType.Q3,
                "Q4": ReportType.ANNUAL,  # Q4用年报代替
                "FY": ReportType.ANNUAL,
            }
            target_type = quarter_map.get(user_quarter.upper())
            
            for report in available:
                if report["year"] == user_year and report["type"] == target_type:
                    return report
        
        # 如果用户只指定了年份
        if user_year:
            # 优先返回该年份的最新报告
            for report in available:
                if report["year"] == user_year:
                    return report
        
        # 返回最新的可用报告
        return available[0]
    
    @staticmethod
    def get_search_date_range(report_info: Dict) -> Tuple[str, str]:
        """
        根据报告信息获取搜索日期范围
        
        Returns:
            (start_date, end_date) 格式: "YYYY-MM-DD"
        """
        year = report_info["year"]
        report_type = report_info["type"]
        
        if report_type == ReportType.ANNUAL:
            # 年报：前一年12月到次年5月
            start_date = f"{year}-12-01"
            end_date = f"{year + 1}-05-31"
        elif report_type == ReportType.Q1:
            # 一季报：当年3月到5月
            start_date = f"{year}-03-01"
            end_date = f"{year}-05-31"
        elif report_type == ReportType.SEMI_ANNUAL:
            # 中报：当年7月到9月
            start_date = f"{year}-07-01"
            end_date = f"{year}-09-30"
        elif report_type == ReportType.Q3:
            # 三季报：当年9月到11月
            start_date = f"{year}-09-01"
            end_date = f"{year}-11-30"
        else:
            # 默认范围
            start_date = f"{year}-01-01"
            end_date = f"{year + 1}-12-31"
        
        return start_date, end_date
    
    @staticmethod
    def get_report_title_keywords(report_info: Dict) -> List[str]:
        """
        获取报告标题关键词列表（用于匹配）
        
        Returns:
            关键词列表，按优先级排序
        """
        year = report_info["year"]
        report_type = report_info["type"]
        
        if report_type == ReportType.ANNUAL:
            return [
                f"{year}年年度报告",
                f"{year}年度报告",
                f"{year}年报",
            ]
        elif report_type == ReportType.Q1:
            return [
                f"{year}年第一季度报告",
                f"{year}年一季度报告",
                f"{year}年一季报",
            ]
        elif report_type == ReportType.SEMI_ANNUAL:
            return [
                f"{year}年半年度报告",
                f"{year}年中期报告",
                f"{year}年中报",
                f"{year}半年报",
            ]
        elif report_type == ReportType.Q3:
            return [
                f"{year}年第三季度报告",
                f"{year}年三季度报告",
                f"{year}年三季报",
            ]
        
        return []


# 测试代码
if __name__ == "__main__":
    import json
    
    print("="*60)
    print("财报时间规则测试")
    print("="*60)
    
    # 测试当前时间可用的报告
    print("\n当前时间可用的报告类型:")
    available = ReportTimingService.get_available_reports()
    for i, report in enumerate(available, 1):
        print(f"{i}. {report['description']} (优先级: {report['priority']})")
    
    # 测试最佳报告选择
    print("\n最佳报告选择:")
    best = ReportTimingService.get_best_report_type()
    print(f"推荐: {best['description']}")
    
    # 测试搜索日期范围
    start, end = ReportTimingService.get_search_date_range(best)
    print(f"搜索日期范围: {start} ~ {end}")
    
    # 测试标题关键词
    keywords = ReportTimingService.get_report_title_keywords(best)
    print(f"标题关键词: {keywords}")
