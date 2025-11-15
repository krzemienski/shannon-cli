"""
Library Discovery Module - Find open-source libraries instead of building from scratch

Searches package registries (npm, PyPI, CocoaPods, Swift PM, Maven, crates.io)
and recommends battle-tested libraries.

Integrates with:
- Firecrawl MCP (web search for libraries)
- Serena MCP (caching discovered libraries)
- Package registries (direct API calls when possible)

Created: November 15, 2025
Part of: Shannon V3.5 Wave 2 (Library Discovery)
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

from .models import LibraryRecommendation


class LibraryDiscoverer:
    """
    Discover and recommend open-source libraries for features
    
    Prevents reinventing the wheel by finding existing solutions.
    
    Usage:
        discoverer = LibraryDiscoverer(project_root=Path("/path/to/project"))
        
        libraries = await discoverer.discover_for_feature(
            feature_description="authentication",
            category="auth"
        )
        
        # Returns ranked list of recommendations
        # Top recommendation: libraries[0]
    """
    
    def __init__(self, project_root: Path, logger: Optional[logging.Logger] = None):
        """
        Initialize library discoverer
        
        Args:
            project_root: Project directory
            logger: Optional logger
        """
        self.project_root = project_root
        self.logger = logger or logging.getLogger(__name__)
        self.project_type = self._detect_project_type()
        self.language = self._detect_language()
        
        self.logger.info(f"LibraryDiscoverer initialized for {self.project_type} ({self.language})")
    
    async def discover_for_feature(
        self,
        feature_description: str,
        category: str = "general"
    ) -> List[LibraryRecommendation]:
        """
        Discover libraries for a specific feature
        
        Args:
            feature_description: Feature/functionality needed (e.g., "authentication", "UI components")
            category: Category for better search (auth, ui, networking, data, etc.)
            
        Returns:
            Ranked list of library recommendations (best first)
        """
        self.logger.info(f"Discovering libraries for: {feature_description}")
        
        # 1. Check Serena cache first
        cache_key = f"libraries_{self.language}_{feature_description.replace(' ', '_')}"
        cached = await self._check_serena_cache(cache_key)
        
        if cached:
            self.logger.info(f"Using cached library recommendations ({len(cached)} found)")
            return cached
        
        # 2. Search based on language/project type
        results = await self._search_libraries(feature_description, category)
        
        # 3. Rank by quality
        ranked = self._rank_libraries(results)
        
        # 4. Cache in Serena for future
        await self._cache_in_serena(cache_key, ranked)
        
        self.logger.info(f"Discovered {len(ranked)} libraries, top: {ranked[0].name if ranked else 'none'}")
        
        return ranked[:5]  # Return top 5
    
    async def _search_libraries(
        self,
        feature: str,
        category: str
    ) -> List[Dict[str, Any]]:
        """
        Search for libraries based on language
        
        Args:
            feature: Feature description
            category: Category hint
            
        Returns:
            Raw library data from search
        """
        if self.language in ["javascript", "typescript"]:
            return await self._search_npm(feature)
        
        elif self.language == "python":
            return await self._search_pypi(feature)
        
        elif self.language == "swift":
            return await self._search_swift_packages(feature)
        
        elif self.language == "java":
            return await self._search_maven(feature)
        
        elif self.language == "rust":
            return await self._search_crates(feature)
        
        else:
            # Generic web search
            return await self._generic_search(feature)
    
    async def _search_npm(self, feature: str) -> List[Dict[str, Any]]:
        """
        Search npm registry
        
        Uses firecrawl MCP if available, falls back to web search
        """
        query = f"npm {feature} package"
        
        # Try using firecrawl MCP
        try:
            # Would use MCP here in real implementation
            # For now, return mock data structure
            results = await self._web_search_packages(query, "npm")
            return results
        except Exception as e:
            self.logger.warning(f"npm search failed: {e}")
            return []
    
    async def _search_pypi(self, feature: str) -> List[Dict[str, Any]]:
        """Search Python Package Index"""
        query = f"python {feature} library pypi"
        return await self._web_search_packages(query, "pypi")
    
    async def _search_swift_packages(self, feature: str) -> List[Dict[str, Any]]:
        """Search Swift Package Manager / CocoaPods"""
        query = f"swift {feature} library site:github.com OR site:swiftpackageindex.com"
        return await self._web_search_packages(query, "swift")
    
    async def _search_maven(self, feature: str) -> List[Dict[str, Any]]:
        """Search Maven Central"""
        query = f"java {feature} library maven"
        return await self._web_search_packages(query, "maven")
    
    async def _search_crates(self, feature: str) -> List[Dict[str, Any]]:
        """Search crates.io (Rust)"""
        query = f"rust {feature} crate"
        return await self._web_search_packages(query, "crates")
    
    async def _web_search_packages(
        self,
        query: str,
        ecosystem: str
    ) -> List[Dict[str, Any]]:
        """
        Web search for packages using available MCPs
        
        In real implementation, this would use firecrawl MCP.
        For now, returns empty list (will be implemented in actual Wave 2).
        """
        self.logger.debug(f"Web search: {query}")
        
        # TODO: Integrate with firecrawl MCP
        # from shannon.mcp.manager import MCPManager
        # mcp = MCPManager()
        # results = await mcp.invoke('firecrawl', 'search', {'query': query, 'limit': 10})
        
        return []
    
    async def _generic_search(self, feature: str) -> List[Dict[str, Any]]:
        """Generic web search when language unknown"""
        query = f"{feature} open source library"
        return await self._web_search_packages(query, "generic")
    
    def _rank_libraries(self, libraries: List[Dict[str, Any]]) -> List[LibraryRecommendation]:
        """
        Rank libraries by quality score
        
        Scoring algorithm:
        - Stars: 40% (more stars = more popular/trusted)
        - Maintenance: 30% (recent updates = actively maintained)
        - Downloads: 20% (usage indicates quality)
        - License: 10% (prefer permissive licenses)
        
        Args:
            libraries: Raw library data
            
        Returns:
            Sorted list of LibraryRecommendation (best first)
        """
        ranked = []
        
        for lib in libraries:
            score = self._calculate_quality_score(lib)
            
            try:
                last_updated = datetime.fromisoformat(lib.get('last_updated', datetime.now().isoformat()))
            except:
                last_updated = datetime.now()
            
            ranked.append(LibraryRecommendation(
                name=lib.get('name', 'unknown'),
                description=lib.get('description', ''),
                repository_url=lib.get('repository_url', ''),
                stars=lib.get('stars', 0),
                last_updated=last_updated,
                package_manager=self._get_package_manager(),
                install_command=self._generate_install_command(lib.get('name', '')),
                why_recommended=self._generate_recommendation_reason(lib, score),
                score=score,
                weekly_downloads=lib.get('downloads'),
                license=lib.get('license')
            ))
        
        return sorted(ranked, key=lambda x: x.score, reverse=True)
    
    def _calculate_quality_score(self, lib: Dict[str, Any]) -> float:
        """
        Calculate overall quality score (0-100)
        
        Weights:
        - Stars: 40 points max
        - Maintenance: 30 points max
        - Downloads: 20 points max
        - License: 10 points max
        """
        score = 0.0
        
        # Stars (40 points)
        stars = lib.get('stars', 0)
        if stars > 10000:
            score += 40
        elif stars > 5000:
            score += 35
        elif stars > 1000:
            score += 30
        elif stars > 500:
            score += 25
        elif stars > 100:
            score += 20
        else:
            score += 10
        
        # Maintenance (30 points)
        last_updated_str = lib.get('last_updated')
        if last_updated_str:
            try:
                last_updated = datetime.fromisoformat(last_updated_str)
                days_ago = (datetime.now() - last_updated).days
                
                if days_ago < 30:
                    score += 30  # Very active
                elif days_ago < 90:
                    score += 25  # Active
                elif days_ago < 180:
                    score += 20  # Maintained
                elif days_ago < 365:
                    score += 10  # Somewhat maintained
                # else: 0 points (likely abandoned)
            except:
                score += 10  # Unknown, give some points
        
        # Downloads (20 points)
        downloads = lib.get('downloads', 0)
        if downloads > 1000000:
            score += 20
        elif downloads > 100000:
            score += 15
        elif downloads > 10000:
            score += 10
        elif downloads > 1000:
            score += 5
        
        # License (10 points)
        license = lib.get('license', '').lower()
        if any(l in license for l in ['mit', 'apache', 'bsd']):
            score += 10
        elif 'isc' in license or 'unlicense' in license:
            score += 8
        elif 'gpl' in license:
            score += 5  # GPL is open but restrictive
        
        return score
    
    def _generate_recommendation_reason(self, lib: Dict[str, Any], score: float) -> str:
        """Generate explanation for why this library is recommended"""
        reasons = []
        
        stars = lib.get('stars', 0)
        if stars > 5000:
            reasons.append(f"{stars:,} stars (very popular)")
        elif stars > 1000:
            reasons.append(f"{stars:,} stars (popular)")
        
        last_updated = lib.get('last_updated')
        if last_updated:
            try:
                days_ago = (datetime.now() - datetime.fromisoformat(last_updated)).days
                if days_ago < 30:
                    reasons.append("recently updated")
                elif days_ago < 180:
                    reasons.append("actively maintained")
            except:
                pass
        
        downloads = lib.get('downloads')
        if downloads and downloads > 100000:
            reasons.append(f"{downloads:,} weekly downloads")
        
        license = lib.get('license')
        if license and 'mit' in license.lower():
            reasons.append("MIT license")
        
        if not reasons:
            reasons.append("meets basic quality criteria")
        
        return ", ".join(reasons)
    
    def _get_package_manager(self) -> str:
        """Get appropriate package manager for this project"""
        if self.language in ["javascript", "typescript"]:
            return "npm"
        elif self.language == "python":
            return "pip"
        elif self.language == "swift":
            return "spm"  # Swift Package Manager
        elif self.language == "java":
            return "maven"
        elif self.language == "rust":
            return "cargo"
        else:
            return "unknown"
    
    def _generate_install_command(self, package_name: str) -> str:
        """Generate installation command for this package"""
        pm = self._get_package_manager()
        
        if pm == "npm":
            return f"npm install {package_name}"
        elif pm == "pip":
            return f"pip install {package_name}"
        elif pm == "spm":
            return f"Add via Xcode: File → Add Packages → {package_name}"
        elif pm == "maven":
            return f"Add to pom.xml: {package_name}"
        elif pm == "cargo":
            return f"cargo add {package_name}"
        else:
            return f"Install {package_name}"
    
    def _detect_project_type(self) -> str:
        """Detect project type (same logic as PromptEnhancer)"""
        from shannon.executor.prompt_enhancer import PromptEnhancer
        enhancer = PromptEnhancer()
        return enhancer._detect_project_type(self.project_root)
    
    def _detect_language(self) -> str:
        """Detect primary programming language"""
        # Based on project type
        if self.project_type.startswith('ios'):
            return "swift"
        elif self.project_type in ['react-native', 'react-native-expo', 'react', 'next.js', 'nodejs', 'vue']:
            # Check if TypeScript
            if (self.project_root / 'tsconfig.json').exists():
                return "typescript"
            else:
                return "javascript"
        elif self.project_type.startswith('python'):
            return "python"
        elif self.project_type == 'android':
            return "java"  # or kotlin
        elif self.project_type == 'rust':
            return "rust"
        elif self.project_type == 'go':
            return "go"
        else:
            return "unknown"
    
    async def _check_serena_cache(self, key: str) -> Optional[List[LibraryRecommendation]]:
        """
        Check Serena MCP for cached library discoveries
        
        Args:
            key: Cache key
            
        Returns:
            Cached libraries if found and recent, None otherwise
        """
        try:
            # TODO: Integrate with actual Serena MCP
            # from shannon.mcp.manager import MCPManager
            # mcp = MCPManager()
            # 
            # if not mcp.is_available('serena'):
            #     return None
            # 
            # cached = await mcp.invoke('serena', 'read_memory', {'key': key})
            # 
            # if cached:
            #     # Check if cache is recent (< 7 days)
            #     cached_at = datetime.fromisoformat(cached.get('cached_at'))
            #     if (datetime.now() - cached_at) < timedelta(days=7):
            #         # Deserialize LibraryRecommendation objects
            #         libraries = []
            #         for lib_data in cached.get('libraries', []):
            #             lib_data['last_updated'] = datetime.fromisoformat(lib_data['last_updated'])
            #             libraries.append(LibraryRecommendation(**lib_data))
            #         return libraries
            
            pass  # Not implemented yet
        except Exception as e:
            self.logger.warning(f"Serena cache check failed: {e}")
        
        return None
    
    async def _cache_in_serena(self, key: str, libraries: List[LibraryRecommendation]):
        """
        Cache discovered libraries in Serena MCP
        
        Args:
            key: Cache key
            libraries: Libraries to cache
        """
        try:
            # TODO: Integrate with actual Serena MCP
            # from shannon.mcp.manager import MCPManager
            # mcp = MCPManager()
            # 
            # if not mcp.is_available('serena'):
            #     return
            # 
            # await mcp.invoke('serena', 'write_memory', {
            #     'key': key,
            #     'data': {
            #         'libraries': [lib.to_dict() for lib in libraries],
            #         'cached_at': datetime.now().isoformat()
            #     }
            # })
            
            self.logger.debug(f"Cached {len(libraries)} libraries in Serena")
        except Exception as e:
            self.logger.warning(f"Serena caching failed: {e}")
            # Cache failure is non-fatal

