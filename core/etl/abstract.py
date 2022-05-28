import abc


class AbstractETL(abc.ABC):
    async def execute(self):
        data = await self._extract()
        data = await self._transform(data)
        return await self._load(data)

    @abc.abstractmethod
    async def _extract(self):
        pass

    @abc.abstractmethod
    async def _transform(self, data):
        return data

    @abc.abstractmethod
    async def _load(self, data):
        return data
